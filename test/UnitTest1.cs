using System;
using ClassLib;
using ConsoleDI.Example;
using Microsoft.Extensions.DependencyInjection;
using Xunit;
using Microsoft.Extensions.Hosting;

namespace MyFirstUnitTests
{
    public class UnitTest1
    {
        [Fact]
        public void Test1()
        {

        }
        
        [Theory]
        [InlineData(3)]
        [InlineData(5)]
        // [InlineData(6)]
        public void MyFirstTheory(int value)
        {
            Assert.True(IsOdd(value));
        }
        
        bool IsOdd(int value)
        {
            return value % 2 == 1;
        }

        [Fact]
        public void LanguageWorks()
        {
            var builder = Host.CreateApplicationBuilder();
            builder.Services.AddSingleton<IParser, Parser>();
            using var host = builder.Build();
            
            // or just use ServiceCollection
            // using serviceProvider
            
            // await host.RunAsync();

            using var serviceScope = host.Services.CreateScope();
            var provider = serviceScope.ServiceProvider;
            
            var parser = provider.GetRequiredService<IParser>();
            
            // var parser = new Parser();
            var language = new Language(parser);
            Assert.Equal(5, language.Eval("text"));
        }
    }
}
