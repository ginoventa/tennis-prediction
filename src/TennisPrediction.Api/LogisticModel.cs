namespace TennisPrediction.Api;

internal sealed class LogisticModel
{
    private readonly double[] _means;
    private readonly double[] _scales;
    private readonly double[] _coefficients;
    private readonly double _intercept;

    public LogisticModel(double[] means, double[] scales, double[] coefficients, double intercept)
    {
        _means = means;
        _scales = scales;
        _coefficients = coefficients;
        _intercept = intercept;
    }

    public double PredictProbability(double[] x)
    {
        var z = _intercept;
        for (var j = 0; j < _coefficients.Length; j++)
        {
            z += _coefficients[j] * ((x[j] - _means[j]) / _scales[j]);
        }

        return Sigmoid(z);
    }

    public IReadOnlyList<double> FeatureContributions(double[] x)
    {
        return _coefficients
            .Select((coefficient, index) => coefficient * ((x[index] - _means[index]) / _scales[index]))
            .ToList();
    }

    private static double Sigmoid(double z)
    {
        if (z >= 0)
        {
            var exp = Math.Exp(-z);
            return 1 / (1 + exp);
        }

        var negativeExp = Math.Exp(z);
        return negativeExp / (1 + negativeExp);
    }
}
