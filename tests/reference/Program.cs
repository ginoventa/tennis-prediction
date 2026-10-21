using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.FileProviders;
using TennisPrediction.Api;
using System.Text.Json;
var service = new TennisModelService(new Env(args[0]));
var players = service.SearchPlayers(null, 300);
var cases = new List<object>();
for (var i = 0; i < 60; i++) {
    var p1 = players[(i * 7) % players.Count];
    var p2 = players[(i * 13 + 1) % players.Count];
    if (p1.Id == p2.Id) continue;
    foreach (var surface in new[] { "Hard", "Clay", "Grass", "Carpet" }) {
        var request = new PredictRequest(p1.Id, p2.Id, surface, null);
        cases.Add(new { request, expected = service.Predict(request) });
    }
}
Console.WriteLine(JsonSerializer.Serialize(cases, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower }));
class Env(string root) : IWebHostEnvironment {
 public string ContentRootPath {get;set;} = root;
 public string WebRootPath {get;set;} = "";
 public string ApplicationName {get;set;} = "Parity";
 public string EnvironmentName {get;set;} = "Development";
 public IFileProvider ContentRootFileProvider {get;set;} = new NullFileProvider();
 public IFileProvider WebRootFileProvider {get;set;} = new NullFileProvider();
}
