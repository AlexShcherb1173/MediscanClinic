from django import forms


class FeedbackForm(forms.Form):
    name = forms.CharField(label="Имя", max_length=120)
    contact = forms.CharField(label="Телефон или Email", max_length=120)
    message = forms.CharField(label="Сообщение", widget=forms.Textarea, max_length=2000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tailwind-классы
        base = "w-full rounded-xl border-slate-200 focus:border-slate-400 focus:ring-0"
        self.fields["name"].widget.attrs.update({"class": base, "placeholder": "Например: Анна"})
        self.fields["contact"].widget.attrs.update({"class": base, "placeholder": "+7… или email@…"})
        self.fields["message"].widget.attrs.update({
            "class": base,
            "rows": 4,
            "placeholder": "Например: хочу уточнить подготовку к УЗИ...",
        })