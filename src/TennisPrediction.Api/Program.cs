using System.Text.Json;
using TennisPrediction.Api;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddSingleton<TennisModelService>();
builder.Services.Configure<ModelTrainingOptions>(builder.Configuration.GetSection("ModelTraining"));
builder.Services.AddHostedService<ModelTrainingWorker>();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new()
    {
        Title = "Tennis Prediction API",
        Version = "v1",
        Description = "API para prever probabilidades de vitoria em partidas WTA."
    });
});
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
});
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy => policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod());
});

var app = builder.Build();

// Force model loading during startup so /health reflects the real state.
app.Services.GetRequiredService<TennisModelService>();

app.UseCors();
app.UseSwagger();
app.UseSwaggerUI(options =>
{
    options.SwaggerEndpoint("/swagger/v1/swagger.json", "Tennis Prediction API v1");
    options.RoutePrefix = "swagger";
});
app.UseDefaultFiles();
app.UseStaticFiles(new StaticFileOptions
{
    OnPrepareResponse = context =>
    {
        context.Context.Response.Headers.CacheControl = "no-cache, no-store, must-revalidate";
        context.Context.Response.Headers.Pragma = "no-cache";
        context.Context.Response.Headers.Expires = "0";
    }
});

app.MapGet("/health", (TennisModelService model) => Results.Ok(model.GetHealth()));

app.MapGet("/players", (TennisModelService model, string? search, int? limit) =>
{
    return Results.Ok(model.SearchPlayers(search, limit ?? 80));
});

app.MapGet("/metrics", (TennisModelService model) => Results.Ok(model.GetMetrics()));
app.MapGet("/accuracy", (TennisModelService model) => Results.Ok(model.GetAccuracySummary()));

app.MapPost("/predict", (PredictRequest request, TennisModelService model) =>
{
    var result = model.Predict(request);
    return result is null
        ? Results.BadRequest(new { error = "Jogadoras inválidas ou iguais. Use GET /players para consultar IDs disponíveis." })
        : Results.Ok(result);
});

app.MapFallbackToFile("index.html");

app.Run();
