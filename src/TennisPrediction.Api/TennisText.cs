using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace TennisPrediction.Api;

internal static class TennisText
{
    public static string NormalizeSurface(string? surface)
    {
        return string.IsNullOrWhiteSpace(surface) ? "Hard" : CultureInfo.InvariantCulture.TextInfo.ToTitleCase(surface.Trim().ToLowerInvariant());
    }

    public static string AbbreviatePlayerName(string name)
    {
        var parts = name.Replace("_", " ")
            .Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

        if (parts.Length < 2)
        {
            return name.Trim();
        }

        var initials = string.Concat(parts.Take(parts.Length - 1).Select(part => $"{char.ToUpperInvariant(part[0])}."));
        return $"{parts[^1]} {initials}";
    }

    public static string MakeId(string name)
    {
        var normalized = RemoveDiacritics(name).ToLowerInvariant();
        return Regex.Replace(normalized, "[^a-z0-9]+", "-").Trim('-');
    }

    public static string PairKey(string a, string b, out bool reversed)
    {
        reversed = string.Compare(a, b, StringComparison.OrdinalIgnoreCase) > 0;
        return reversed ? $"{b}\u001f{a}" : $"{a}\u001f{b}";
    }

    private static string RemoveDiacritics(string text)
    {
        var normalized = text.Normalize(NormalizationForm.FormD);
        var builder = new StringBuilder();
        foreach (var c in normalized)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark)
            {
                builder.Append(c);
            }
        }

        return builder.ToString().Normalize(NormalizationForm.FormC);
    }
}
