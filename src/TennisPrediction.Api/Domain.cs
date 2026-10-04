namespace TennisPrediction.Api;

public sealed record PredictRequest(
    string Player_1_Id,
    string Player_2_Id,
    string Surface,
    DateOnly? Match_Date);

public sealed record PlayerDto(
    string Id,
    string Name,
    int Matches,
    int Wins,
    double WinRate,
    int? LastRank,
    int? LastPoints);

public sealed record DriverDto(string Factor, string Impact);

public sealed record PredictionResponse(
    string Player_1,
    string Player_2,
    double Win_Probability_P1,
    double Win_Probability_P2,
    PowerIndexDto Power_Index,
    IReadOnlyList<DriverDto> Key_Drivers,
    FeatureSnapshotDto Features);

public sealed record PowerIndexDto(double Player_1, double Player_2);

public sealed record FeatureSnapshotDto(
    double Rank_Diff,
    double Points_Diff,
    double Recent_Form_Diff,
    double Surface_Win_Rate_Diff,
    double Head_To_Head_Diff,
    double Experience_Diff);

public sealed record ModelMetricsDto(
    int TotalMatches,
    int TrainingRows,
    int TestRows,
    double Accuracy,
    double Precision,
    double Recall,
    double F1,
    double RocAuc,
    double LogLoss,
    DateOnly? FirstMatch,
    DateOnly? LastMatch,
    IReadOnlyList<string> Features);

public sealed record AccuracySummaryDto(
    double Accuracy,
    double BaselineAccuracy,
    double Lift,
    int CorrectPredictions,
    int TestRows);
