def theme_colors(request):
    """Expose the dark theme palette to every template as `THEME`."""
    return {
        "THEME": {
            "bg": "#0D1117",
            "card": "#161B22",
            "border": "#30363D",
            "primary": "#2F81F7",
            "text": "#E6EDF3",
            "text_secondary": "#8B949E",
            "success": "#3FB950",
            "warning": "#D29922",
            "danger": "#F85149",
        }
    }
