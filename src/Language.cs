namespace ClassLib;

public class Language
{
    private IParser _parser;
    
    public Language(IParser parser)
    {
        _parser = parser;
    }

    public int Eval(string text)
    {
        return _parser.Parse(text);
    }
}