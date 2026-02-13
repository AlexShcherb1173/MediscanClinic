from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        label="Ваше имя",
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Ваше имя"}),
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    message = forms.CharField(
        label="Сообщение",
        required=True,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Сообщение"}),
    )

    def clean_name(self):
        v = (self.cleaned_data.get("name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Введите имя (минимум 2 символа).")
        return v