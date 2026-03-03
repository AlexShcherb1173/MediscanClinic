// static/js/feedback-modal.js
(() => {
  const modal = document.getElementById("feedback-modal");
  const dialog = document.getElementById("feedback-dialog");
  const openers = document.querySelectorAll("[data-open-feedback]");
  const closers = modal?.querySelectorAll("[data-feedback-close]") || [];
  const form = document.getElementById("feedback-form");
  const submitBtn = document.getElementById("feedback-submit");
  const btnText = document.getElementById("feedback-btn-text");
  const btnLoader = document.getElementById("feedback-btn-loader");
  const toastRoot = document.getElementById("toast-root");

  // Если обязательные элементы не найдены — выходим, чтобы не падать в консоли
  if (!modal || !dialog || !form || !submitBtn || !toastRoot) return;

  // ---------- Toast (всплывающие уведомления) ----------
  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className =
      "pointer-events-auto max-w-sm rounded-2xl border px-4 py-3 shadow-lg " +
      "bg-white text-slate-900 border-slate-200 " +
      "opacity-0 translate-y-2 transition-all duration-200";

    // Лёгкое визуальное различие статусов
    if (type === "success") el.className += " ring-1 ring-green-200";
    if (type === "error") el.className += " ring-1 ring-red-200";

    el.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="mt-0.5 text-sm font-semibold">
          ${type === "success" ? "✅" : type === "error" ? "⚠️" : "ℹ️"}
        </div>
        <div class="text-sm leading-relaxed">${message}</div>
        <button class="ml-auto text-slate-400 hover:text-slate-700 transition" aria-label="Close">✕</button>
      </div>
    `;

    // Закрытие по кнопке "✕"
    el.querySelector("button")?.addEventListener("click", () => removeToast(el));
    toastRoot.appendChild(el);

    // Анимация появления (через следующий кадр)
    requestAnimationFrame(() => {
      el.classList.remove("opacity-0", "translate-y-2");
      el.classList.add("opacity-100", "translate-y-0");
    });

    // Автозакрытие через 4.5 секунды
    const t = setTimeout(() => removeToast(el), 4500);
    el.dataset.timer = String(t);
  }

  function removeToast(el) {
    const t = Number(el.dataset.timer || 0);
    if (t) clearTimeout(t);

    // Анимация скрытия перед удалением
    el.classList.remove("opacity-100", "translate-y-0");
    el.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => el.remove(), 200);
  }

  // ---------- Открытие/закрытие модального окна ----------
  function onEsc(e) {
    // Закрываем по Escape
    if (e.key === "Escape") closeModal();
  }

  function openModal() {
    // Показываем модалку
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");

    // Ищем бекдроп (затемнение) внутри модалки
    const bg = modal.querySelector("div.absolute");

    // Плавная анимация появления (бекдроп + диалог)
    requestAnimationFrame(() => {
      bg?.classList.remove("opacity-0");
      bg?.classList.add("opacity-100");
      dialog.classList.remove("opacity-0", "translate-y-2");
      dialog.classList.add("opacity-100", "translate-y-0");
    });

    // Фокус на первое поле (удобство для пользователя)
    const first = form.querySelector('input[name="name"]');
    setTimeout(() => first?.focus(), 60);

    // Навешиваем обработчик Escape
    document.addEventListener("keydown", onEsc);
  }

  function closeModal() {
    // Находим бекдроп (затемнение)
    const bg = modal.querySelector("div.absolute");

    // Анимация скрытия (бекдроп + диалог)
    bg?.classList.remove("opacity-100");
    bg?.classList.add("opacity-0");
    dialog.classList.remove("opacity-100", "translate-y-0");
    dialog.classList.add("opacity-0", "translate-y-2");

    // После анимации — скрываем модалку полностью
    setTimeout(() => {
      modal.classList.add("hidden");
      modal.setAttribute("aria-hidden", "true");
    }, 200);

    // Снимаем обработчик Escape
    document.removeEventListener("keydown", onEsc);
  }

  // Кнопки-открыватели
  openers.forEach((btn) => btn.addEventListener("click", openModal));

  // Кнопки-закрыватели (включая клик по фону, если он помечен data-feedback-close)
  closers.forEach((btn) => btn.addEventListener("click", closeModal));

  // ---------- Ripple-эффект на кнопке отправки ----------
  function addRipple(e, button) {
    const rect = button.getBoundingClientRect();
    const x = (e.clientX ?? rect.width / 2) - rect.left;
    const y = (e.clientY ?? rect.height / 2) - rect.top;

    const span = document.createElement("span");
    span.className = "ripple";
    span.style.left = `${x}px`;
    span.style.top = `${y}px`;

    button.appendChild(span);
    setTimeout(() => span.remove(), 650);
  }

  submitBtn.addEventListener("pointerdown", (e) => addRipple(e, submitBtn));

  // ---------- Вспомогательные функции для UI/ошибок ----------
  function clearErrors() {
    // Скрываем ошибки конкретных полей
    form.querySelectorAll("[data-err]").forEach((el) => {
      el.classList.add("hidden");
      el.textContent = "";
    });

    // Скрываем “общую” ошибку формы (non-field error), если она есть
    const nf = form.querySelector("[data-nf]");
    if (nf) {
      nf.classList.add("hidden");
      nf.textContent = "";
    }

    // Убираем красные рамки и ring у полей
    form.querySelectorAll("input, textarea").forEach((el) => {
      el.classList.remove(
        "border-red-300",
        "focus:border-red-500",
        "focus:ring-red-100"
      );
    });
  }

  function showFieldError(name, text) {
    // Показываем ошибку под конкретным полем
    const err = form.querySelector(`[data-err="${name}"]`);
    const field = form.querySelector(`[name="${name}"]`);

    if (err) {
      err.textContent = text;
      err.classList.remove("hidden");
    }
    if (field) {
      field.classList.add(
        "border-red-300",
        "focus:border-red-500",
        "focus:ring-red-100"
      );
    }
  }

  function showNonFieldError(text) {
    // Создаём контейнер под non-field ошибки, если его нет в шаблоне
    let box = form.querySelector("[data-nf]");
    if (!box) {
      box = document.createElement("div");
      box.setAttribute("data-nf", "1");
      box.className =
        "rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 hidden";
      form.prepend(box);
    }

    // Пишем текст и показываем
    box.textContent = text;
    box.classList.remove("hidden");
  }

  function setLoading(loading) {
    // Переводим кнопку в “загрузка/не загрузка”
    submitBtn.disabled = loading;
    submitBtn.classList.toggle("opacity-80", loading);
    submitBtn.classList.toggle("cursor-not-allowed", loading);

    if (btnLoader) btnLoader.classList.toggle("hidden", !loading);
    if (btnText) btnText.textContent = loading ? "Отправка..." : "Отправить";
  }

  function getCsrfToken() {
    // Берём CSRF из скрытого input в форме
    return (
      form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || ""
    );
  }

  // ---------- Парсинг ошибок Django из HTML-ответа ----------
  function parseErrorsFromHtml(htmlText) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, "text/html");

    // 1) Пытаемся вытащить ошибку из “якорей” (#error-... или data-error-for)
    const getErrorTextFor = (fieldName) => {
      const el =
        doc.querySelector(`#error-${fieldName}`) ||
        doc.querySelector(`[data-error-for="${fieldName}"]`);

      if (!el) return "";

      // В Django обычно <ul class="errorlist"><li>...</li></ul>
      const li = el.querySelector("li");
      if (li) return li.textContent.trim();

      // Запасной вариант: берём весь текст контейнера
      return el.textContent.trim();
    };

    const errors = {
      name: getErrorTextFor("name"),
      email: getErrorTextFor("email"),
      message: getErrorTextFor("message"),
      nonField: "",
    };

    // Non-field ошибки Django
    const nf =
      doc.querySelector("#form-non-field-errors") ||
      doc.querySelector("[data-non-field-errors]");

    if (nf) {
      const li = nf.querySelector("li");
      const text = (li ? li.textContent : nf.textContent).trim();
      if (text) errors.nonField = text;
    }

    // 2) Запасной вариант: стандартные Django errorlist рядом с полями
    // (если вдруг шаблон отличается)
    if (!errors.name || !errors.email || !errors.message) {
      doc.querySelectorAll("ul.errorlist").forEach((ul) => {
        const text = ul.textContent.trim();
        if (!text) return;

        // Пробуем определить поле по ближайшему input/textarea
        const wrap = ul.closest("div") || ul.parentElement;
        const input = wrap?.querySelector("input[name], textarea[name]");
        const fname = input?.getAttribute("name");

        if (fname && fname in errors && !errors[fname]) {
          errors[fname] = text;
        } else if (!errors.nonField && !fname) {
          errors.nonField = text;
        }
      });
    }

    // Нормализуем пробелы
    for (const k of Object.keys(errors)) {
      errors[k] = (errors[k] || "").trim();
    }

    return errors;
  }

  // ---------- Плавно скрываем форму при успехе ----------
  function smoothHideForm() {
    const body = document.getElementById("feedback-form-body");
    if (!body) return;

    body.classList.add("transition-all", "duration-200");
    body.classList.add("opacity-0", "translate-y-1");
  }

  // ---------- Отправка формы (fetch) ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();
    setLoading(true);

    try {
      const action = form.getAttribute("action");
      const formData = new FormData(form);

      const resp = await fetch(action, {
        method: "POST",
        body: formData,
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "fetch",
        },
        redirect: "follow",
      });

      // ✅ Успех = Django сделал redirect обратно на страницу
      if (resp.redirected) {
        smoothHideForm();
        toast("Сообщение отправлено! Мы скоро свяжемся с вами.", "success");

        setTimeout(() => {
          // Сбрасываем форму и закрываем модалку
          form.reset();
          const body = document.getElementById("feedback-form-body");
          body?.classList.remove("opacity-0", "translate-y-1");
          closeModal();
        }, 260);

        return;
      }

      // ❌ Ошибки формы: сервер вернул HTML без редиректа
      const html = await resp.text();
      const errs = parseErrorsFromHtml(html);

      let shownAny = false;

      if (errs.nonField) {
        showNonFieldError(errs.nonField);
        shownAny = true;
      }

      ["name", "email", "message"].forEach((field) => {
        if (errs[field]) {
          showFieldError(field, errs[field]);
          shownAny = true;
        }
      });

      toast(
        shownAny ? "Проверьте поля формы." : "Не удалось отправить. Попробуйте ещё раз.",
        "error"
      );
    } catch (err) {
      console.error(err);
      toast("Ошибка сети. Проверьте подключение и попробуйте снова.", "error");
    } finally {
      setLoading(false);
    }
  });
})();