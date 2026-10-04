using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace TennisPrediction.Api;

public sealed class TennisModelService
{
    private static readonly string[] ExpectedFeatureNames =
    [
        "rank_diff",
        "points_diff",
        "recent_form_diff",
        "surface_win_rate_diff",
        "head_to_head_diff",
        "experience_diff",
        "chart_serve_win_diff",
        "chart_total_points_won_diff",
        "chart_return_win_diff",
        "chart_bp_saved_diff",
        "chart_winner_rate_diff",
        "chart_unforced_rate_diff",
        "chart_experience_diff",
        "round",
        "is_slam"
    ];

    private static readonly HashSet<string> Slams = new(StringComparer.OrdinalIgnoreCase)
    {
        "Australian Open",
        "French Open",
        "Wimbledon",
        "US Open"
    };

    private readonly object _sync = new();
    private readonly string _artifactPath;
    private ModelState _state;

    public TennisModelService(IWebHostEnvironment environment)
    {
        var root = FindProjectRoot(environment.ContentRootPath);
        _artifactPath = Path.Combine(root, "artifacts", "model.json");

        if (!File.Exists(_artifactPath))
        {
            throw new FileNotFoundException("Artefato artifacts/model.json não encontrado. Execute: python src/training/train_model.py", _artifactPath);
        }

        _state = LoadState(_artifactPath);
    }

    public void Reload()
    {
        var nextState = LoadState(_artifactPath);
        lock (_sync)
        {
            _state = nextState;
        }
    }

    public object GetHealth()
    {
        var state = GetState();
        return new
        {
            status = "ok",
            model = state.Artifact.ModelType,
            version = state.Artifact.Version,
            generated_at = state.Artifact.GeneratedAt,
            trained_matches = state.Metrics.TrainingRows,
            players = state.PlayersByName.Count,
            features = state.Artifact.FeatureNames
        };
    }

    public ModelMetricsDto GetMetrics() => GetState().Metrics;

    public AccuracySummaryDto GetAccuracySummary() => GetState().AccuracySummary;

    public IReadOnlyList<PlayerDto> SearchPlayers(string? search, int limit)
    {
        var state = GetState();
        var query = state.PlayersByName.Values
            .OrderBy(p => p.Name, StringComparer.OrdinalIgnoreCase)
            .AsEnumerable();

        if (!string.IsNullOrWhiteSpace(search))
        {
            query = query.Where(p => p.Name.Contains(search, StringComparison.OrdinalIgnoreCase));
        }

        return query
            .Take(Math.Clamp(limit, 1, 300))
            .Select(p => p.ToDto())
            .ToList();
    }

    public PredictionResponse? Predict(PredictRequest request)
    {
        var state = GetState();
        var p1 = ResolvePlayer(state, request.Player_1_Id);
        var p2 = ResolvePlayer(state, request.Player_2_Id);
        if (p1 is null || p2 is null || string.Equals(p1, p2, StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var surface = TennisText.NormalizeSurface(request.Surface);
        var x = BuildFeatureVector(
            state,
            p1,
            p2,
            surface,
            state.Artifact.Inference.DefaultRound,
            state.Artifact.Inference.DefaultTournament);
        var probability = state.Model.PredictProbability(x);
        var contributions = state.Model.FeatureContributions(x);

        return new PredictionResponse(
            p1,
            p2,
            Math.Round(probability, 3),
            Math.Round(1 - probability, 3),
            new PowerIndexDto(Math.Round(35 + 65 * probability, 1), Math.Round(35 + 65 * (1 - probability), 1)),
            BuildDrivers(p1, p2, surface, contributions),
            new FeatureSnapshotDto(
                Math.Round(x[0], 2),
                Math.Round(x[1], 2),
                Math.Round(x[2], 3),
                Math.Round(x[3], 3),
                Math.Round(x[4], 3),
                Math.Round(x[5], 3)));
    }

    public static string FindProjectRoot(string contentRoot)
    {
        var dir = new DirectoryInfo(contentRoot);
        while (dir is not null)
        {
            if (Directory.Exists(Path.Combine(dir.FullName, "artifacts")))
            {
                return dir.FullName;
            }

            dir = dir.Parent;
        }

        throw new DirectoryNotFoundException("Raiz do projeto não encontrada.");
    }

    private static ModelArtifact LoadArtifact(string path)
    {
        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        var artifact = JsonSerializer.Deserialize<ModelArtifact>(File.ReadAllText(path, Encoding.UTF8), options)
            ?? throw new InvalidOperationException("Não foi possível ler artifacts/model.json.");

        if (!artifact.FeatureNames.SequenceEqual(ExpectedFeatureNames, StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("O artefato do modelo não usa as features esperadas pelo backend C#.");
        }

        if (artifact.Inference.Players.Length == 0)
        {
            throw new InvalidOperationException("O artefato do modelo não contém dados de inferência. Execute: python src/training/train_model.py");
        }

        return artifact;
    }

    private static ModelState LoadState(string artifactPath)
    {
        var artifact = LoadArtifact(artifactPath);
        var playersByName = BuildPlayerLookup(artifact.Inference.Players);
        var idToName = artifact.Inference.Players.ToDictionary(p => p.Id, p => p.Name, StringComparer.OrdinalIgnoreCase);
        var headToHead = BuildHeadToHead(artifact.Inference.HeadToHead);
        var model = new LogisticModel(artifact.Means, artifact.Scales, artifact.Coefficients, artifact.Intercept);
        var metrics = ToMetrics(artifact.Metrics, artifact.FeatureNames);
        var accuracySummary = BuildAccuracySummary(metrics);

        return new ModelState(
            artifact,
            playersByName,
            headToHead,
            idToName,
            model,
            metrics,
            accuracySummary);
    }

    private ModelState GetState()
    {
        lock (_sync)
        {
            return _state;
        }
    }

    private static ModelMetricsDto ToMetrics(ArtifactMetrics metrics, IReadOnlyList<string> featureNames)
    {
        return new ModelMetricsDto(
            metrics.TotalMatches,
            metrics.TrainingRows,
            metrics.TestRows,
            metrics.Accuracy,
            metrics.Precision,
            metrics.Recall,
            metrics.F1,
            metrics.RocAuc,
            metrics.LogLoss,
            DateOnly.TryParse(metrics.FirstMatch, out var first) ? first : null,
            DateOnly.TryParse(metrics.LastMatch, out var last) ? last : null,
            featureNames);
    }

    private static AccuracySummaryDto BuildAccuracySummary(ModelMetricsDto metrics)
    {
        const double baseline = 0.5;
        var correct = (int)Math.Round(metrics.Accuracy * metrics.TestRows);
        return new AccuracySummaryDto(
            metrics.Accuracy,
            baseline,
            Math.Round(metrics.Accuracy - baseline, 3),
            correct,
            metrics.TestRows);
    }

    private static Dictionary<string, (int p1Wins, int p2Wins)> BuildHeadToHead(IEnumerable<ArtifactHeadToHead> rows)
    {
        var h2h = new Dictionary<string, (int p1Wins, int p2Wins)>(StringComparer.OrdinalIgnoreCase);
        foreach (var row in rows)
        {
            var key = TennisText.PairKey(row.Player1, row.Player2, out var reversed);
            h2h[key] = reversed
                ? (row.Player2Wins, row.Player1Wins)
                : (row.Player1Wins, row.Player2Wins);
        }

        return h2h;
    }

    private static Dictionary<string, ArtifactPlayer> BuildPlayerLookup(IEnumerable<ArtifactPlayer> players)
    {
        var lookup = new Dictionary<string, ArtifactPlayer>(StringComparer.OrdinalIgnoreCase);
        foreach (var player in players.OrderByDescending(p => p.Matches))
        {
            lookup.TryAdd(player.Name, player);
        }

        return lookup;
    }

    private static double[] BuildFeatureVector(ModelState state, string player1, string player2, string surface, int round, string tournament)
    {
        var state1 = state.PlayersByName[player1];
        var state2 = state.PlayersByName[player2];
        var rank1 = state1.LastRank ?? 100;
        var rank2 = state2.LastRank ?? 100;
        var points1 = state1.LastPoints ?? 800;
        var points2 = state2.LastPoints ?? 800;

        var key = TennisText.PairKey(player1, player2, out var reversed);
        var pair = state.HeadToHead.GetValueOrDefault(key);
        var p1Wins = reversed ? pair.p2Wins : pair.p1Wins;
        var p2Wins = reversed ? pair.p1Wins : pair.p2Wins;
        var h2hDiff = p1Wins + p2Wins == 0 ? 0 : (p1Wins - p2Wins) / (double)(p1Wins + p2Wins);

        return
        [
            rank1 - rank2,
            points1 - points2,
            state1.RecentWinRate - state2.RecentWinRate,
            SurfaceWinRate(state1, surface) - SurfaceWinRate(state2, surface),
            h2hDiff,
            Math.Log(1 + state1.Matches) - Math.Log(1 + state2.Matches),
            state1.ChartServeWinRate - state2.ChartServeWinRate,
            state1.ChartTotalPointsWonRate - state2.ChartTotalPointsWonRate,
            state1.ChartReturnWinRate - state2.ChartReturnWinRate,
            state1.ChartBpSavedRate - state2.ChartBpSavedRate,
            state1.ChartWinnerRate - state2.ChartWinnerRate,
            state1.ChartUnforcedRate - state2.ChartUnforcedRate,
            Math.Log(1 + state1.ChartMatches) - Math.Log(1 + state2.ChartMatches),
            round,
            Slams.Contains(tournament) ? 1 : 0
        ];
    }

    private static double SurfaceWinRate(ArtifactPlayer player, string surface)
    {
        return player.SurfaceWinRates.TryGetValue(surface, out var rate) ? rate : player.WinRate;
    }

    private static string? ResolvePlayer(ModelState state, string idOrName)
    {
        if (string.IsNullOrWhiteSpace(idOrName))
        {
            return null;
        }

        var value = idOrName.Trim();
        value = Regex.Replace(value, @"\s+\(\d+\s+jogos\)$", string.Empty, RegexOptions.IgnoreCase).Trim();

        if (state.IdToName.TryGetValue(value, out var name))
        {
            return name;
        }

        return state.PlayersByName.ContainsKey(value) ? value : null;
    }

    private static IReadOnlyList<DriverDto> BuildDrivers(string player1, string player2, string surface, IReadOnlyList<double> contributions)
    {
        var labels = new[]
        {
            "Ranking atual",
            "Pontuação WTA",
            "Momento recente",
            $"Aproveitamento no piso ({surface})",
            "Confronto direto (H2H)",
            "Experiência histórica",
            "Saque charted",
            "Total de pontos vencidos charted",
            "Devolução charted",
            "Break points salvos charted",
            "Winners charted",
            "Erros não forçados charted",
            "Experiência charted",
            "Fase do torneio",
            "Grand Slam"
        };

        return contributions
            .Select((impact, index) => new { impact, label = labels[index] })
            .OrderByDescending(item => Math.Abs(item.impact))
            .Take(3)
            .Select(item =>
            {
                var favored = item.impact >= 0 ? player1 : player2;
                return new DriverDto(item.label, $"{Math.Abs(item.impact) * 100:0.0}% para {favored}");
            })
            .ToList();
    }

    private sealed record ModelState(
        ModelArtifact Artifact,
        Dictionary<string, ArtifactPlayer> PlayersByName,
        Dictionary<string, (int p1Wins, int p2Wins)> HeadToHead,
        Dictionary<string, string> IdToName,
        LogisticModel Model,
        ModelMetricsDto Metrics,
        AccuracySummaryDto AccuracySummary);
}
