using System.Text.Json.Serialization;

namespace TennisPrediction.Api;

internal sealed class ModelArtifact
{
    [JsonPropertyName("version")]
    public required string Version { get; init; }

    [JsonPropertyName("model_type")]
    public required string ModelType { get; init; }

    [JsonPropertyName("generated_at")]
    public required string GeneratedAt { get; init; }

    [JsonPropertyName("feature_names")]
    public required string[] FeatureNames { get; init; }

    [JsonPropertyName("means")]
    public required double[] Means { get; init; }

    [JsonPropertyName("scales")]
    public required double[] Scales { get; init; }

    [JsonPropertyName("coefficients")]
    public required double[] Coefficients { get; init; }

    [JsonPropertyName("intercept")]
    public required double Intercept { get; init; }

    [JsonPropertyName("metrics")]
    public required ArtifactMetrics Metrics { get; init; }

    [JsonPropertyName("inference")]
    public required ArtifactInference Inference { get; init; }
}

internal sealed class ArtifactMetrics
{
    [JsonPropertyName("total_matches")]
    public int TotalMatches { get; init; }

    [JsonPropertyName("training_rows")]
    public int TrainingRows { get; init; }

    [JsonPropertyName("test_rows")]
    public int TestRows { get; init; }

    [JsonPropertyName("accuracy")]
    public double Accuracy { get; init; }

    [JsonPropertyName("precision")]
    public double Precision { get; init; }

    [JsonPropertyName("recall")]
    public double Recall { get; init; }

    [JsonPropertyName("f1")]
    public double F1 { get; init; }

    [JsonPropertyName("roc_auc")]
    public double RocAuc { get; init; }

    [JsonPropertyName("log_loss")]
    public double LogLoss { get; init; }

    [JsonPropertyName("first_match")]
    public string? FirstMatch { get; init; }

    [JsonPropertyName("last_match")]
    public string? LastMatch { get; init; }
}

internal sealed class ArtifactInference
{
    [JsonPropertyName("players")]
    public required ArtifactPlayer[] Players { get; init; }

    [JsonPropertyName("head_to_head")]
    public required ArtifactHeadToHead[] HeadToHead { get; init; }

    [JsonPropertyName("default_round")]
    public int DefaultRound { get; init; } = 3;

    [JsonPropertyName("default_tournament")]
    public string DefaultTournament { get; init; } = string.Empty;
}

internal sealed class ArtifactPlayer
{
    [JsonPropertyName("id")]
    public required string Id { get; init; }

    [JsonPropertyName("name")]
    public required string Name { get; init; }

    [JsonPropertyName("matches")]
    public int Matches { get; init; }

    [JsonPropertyName("wins")]
    public int Wins { get; init; }

    [JsonPropertyName("win_rate")]
    public double WinRate { get; init; }

    [JsonPropertyName("last_rank")]
    public int? LastRank { get; init; }

    [JsonPropertyName("last_points")]
    public int? LastPoints { get; init; }

    [JsonPropertyName("recent_win_rate")]
    public double RecentWinRate { get; init; }

    [JsonPropertyName("surface_win_rates")]
    public required Dictionary<string, double> SurfaceWinRates { get; init; }

    [JsonPropertyName("chart_serve_win_rate")]
    public double ChartServeWinRate { get; init; }

    [JsonPropertyName("chart_return_win_rate")]
    public double ChartReturnWinRate { get; init; }

    [JsonPropertyName("chart_total_points_won_rate")]
    public double ChartTotalPointsWonRate { get; init; }

    [JsonPropertyName("chart_bp_saved_rate")]
    public double ChartBpSavedRate { get; init; }

    [JsonPropertyName("chart_winner_rate")]
    public double ChartWinnerRate { get; init; }

    [JsonPropertyName("chart_unforced_rate")]
    public double ChartUnforcedRate { get; init; }

    [JsonPropertyName("chart_matches")]
    public int ChartMatches { get; init; }

    public PlayerDto ToDto()
    {
        return new PlayerDto(
            Id,
            Name,
            Matches,
            Wins,
            Math.Round(WinRate, 3),
            LastRank,
            LastPoints);
    }
}

internal sealed class ArtifactHeadToHead
{
    [JsonPropertyName("player_1")]
    public required string Player1 { get; init; }

    [JsonPropertyName("player_2")]
    public required string Player2 { get; init; }

    [JsonPropertyName("player_1_wins")]
    public int Player1Wins { get; init; }

    [JsonPropertyName("player_2_wins")]
    public int Player2Wins { get; init; }
}
