namespace TennisPrediction.Api;

public sealed class ModelTrainingOptions
{
    public bool Enabled { get; init; }

    public int IntervalDays { get; init; } = 7;

    public bool RunOnStartup { get; init; }

    public string PythonExecutable { get; init; } = "python";

    public string ScriptPath { get; init; } = "src/training/train_model.py";
}
