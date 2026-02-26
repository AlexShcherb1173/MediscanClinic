from django import forms


class FeedbackForm(forms.Form):
    """
    Public feedback/contact form used on the website.

    Collects basic contact information from a user:
    - name
    - phone or email
    - message text

    Styling is applied dynamically in `__init__`
    using Tailwind CSS utility classes.
    """

    name = forms.CharField(
        label="Имя",
        max_length=120,
        help_text="Введите ваше имя.",
    )

    contact = forms.CharField(
        label="Телефон или Email",
        max_length=120,
        help_text="Укажите номер телефона или email для связи.",
    )

    message = forms.CharField(
        label="Сообщение",
        widget=forms.Textarea,
        max_length=2000,
        help_text="Введите текст обращения.",
    )

    def __init__(self, *args, **kwargs):
        """
        Initialize form and attach Tailwind CSS classes
        and placeholders to widgets for consistent UI styling.
        """
        super().__init__(*args, **kwargs)

        # Base Tailwind input styles
        base = "w-full rounded-xl border-slate-200 focus:border-slate-400 focus:ring-0"

        self.fields["name"].widget.attrs.update(
            {
                "class": base,
                "placeholder": "Например: Анна",
            }
        )

        self.fields["contact"].widget.attrs.update(
            {
                "class": base,
                "placeholder": "+7… или email@…",
            }
        )

        self.fields["message"].widget.attrs.update(
            {
                "class": base,
                "rows": 4,
                "placeholder": "Например: хочу уточнить подготовку к УЗИ...",
            }
        )