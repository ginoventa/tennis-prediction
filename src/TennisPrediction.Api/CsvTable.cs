using System.Text;

namespace TennisPrediction.Api;

internal static class CsvTable
{
    public static IEnumerable<Dictionary<string, string>> Read(string path)
    {
        using var reader = new StreamReader(path, Encoding.UTF8, detectEncodingFromByteOrderMarks: true);
        var headerLine = reader.ReadLine();
        if (headerLine is null)
        {
            yield break;
        }

        var headers = ParseLine(headerLine).ToArray();
        string? line;
        while ((line = reader.ReadLine()) is not null)
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            var values = ParseLine(line).ToArray();
            var row = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (var i = 0; i < headers.Length; i++)
            {
                row[headers[i]] = i < values.Length ? values[i] : string.Empty;
            }

            yield return row;
        }
    }

    private static IEnumerable<string> ParseLine(string line)
    {
        var value = new StringBuilder();
        var inQuotes = false;

        for (var i = 0; i < line.Length; i++)
        {
            var c = line[i];
            if (c == '"')
            {
                if (inQuotes && i + 1 < line.Length && line[i + 1] == '"')
                {
                    value.Append('"');
                    i++;
                }
                else
                {
                    inQuotes = !inQuotes;
                }
            }
            else if (c == ',' && !inQuotes)
            {
                yield return value.ToString();
                value.Clear();
            }
            else
            {
                value.Append(c);
            }
        }

        yield return value.ToString();
    }
}
