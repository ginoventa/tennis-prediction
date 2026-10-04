using System.Diagnostics;
using Microsoft.Extensions.Options;

namespace TennisPrediction.Api;

public sealed class ModelTrainingWorker : BackgroundService
{
    private readonly IWebHostEnvironment _environment;
    private readonly ILogger<ModelTrainingWorker> _logger;
    private readonly TennisModelService _modelService;
    private readonly ModelTrainingOptions _options;

    public ModelTrainingWorker(
        IWebHostEnvironment environment,
        ILogger<ModelTrainingWorker> logger,
        TennisModelService modelService,
        IOptions<ModelTrainingOptions> options)
    {
        _environment = environment;
        _logger = logger;
        _modelService = modelService;
        _options = options.Value;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (!_options.Enabled)
        {
            _logger.LogInformation("Treinamento automatico do modelo desativado.");
            return;
        }

        if (_options.RunOnStartup)
        {
            await TrainAndReloadAsync(stoppingToken);
        }

        var interval = TimeSpan.FromDays(Math.Max(1, _options.IntervalDays));
        using var timer = new PeriodicTimer(interval);

        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            await TrainAndReloadAsync(stoppingToken);
        }
    }

    private async Task TrainAndReloadAsync(CancellationToken stoppingToken)
    {
        var root = TennisModelService.FindProjectRoot(_environment.ContentRootPath);
        var scriptPath = Path.Combine(root, _options.ScriptPath);

        if (!File.Exists(scriptPath))
        {
            _logger.LogError("Script de treinamento nao encontrado: {ScriptPath}", scriptPath);
            return;
        }

        _logger.LogInformation("Iniciando retreinamento do modelo com {ScriptPath}.", scriptPath);

        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = _options.PythonExecutable,
                Arguments = $"\"{scriptPath}\"",
                WorkingDirectory = root,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            }
        };

        process.Start();
        var outputTask = process.StandardOutput.ReadToEndAsync(stoppingToken);
        var errorTask = process.StandardError.ReadToEndAsync(stoppingToken);
        await process.WaitForExitAsync(stoppingToken);

        var output = await outputTask;
        var error = await errorTask;

        if (process.ExitCode != 0)
        {
            _logger.LogError(
                "Retreinamento falhou com codigo {ExitCode}. Erro: {Error}",
                process.ExitCode,
                error);
            return;
        }

        _modelService.Reload();
        _logger.LogInformation("Modelo retreinado e recarregado com sucesso. Saida: {Output}", output);
    }
}
