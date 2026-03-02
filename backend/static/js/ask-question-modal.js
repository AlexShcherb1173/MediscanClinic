// static/js/ask-question-modal.js
(() => {
  const modal = document.getElementById("askq-modal");
  const dialog = document.getElementById("askq-dialog");
  const openers = document.querySelectorAll("[data-open-ask-question]");
  const form = document.getElementById("askq-form");
  const submitBtn = document.getElementById("askq-submit");
  const btnText = document.getElementById("askq-btn-text");
  const btnLoader = document.getElementById("askq-btn-loader");
  const toastRoot = document.getElementById("toast-root");

  // Если обязательные элементы не найдены — выходим, чтобы не падать в консоли
  if (!modal || !dialog || !form || !submitBtn || !toastRoot) return;

  const closers = modal.querySelectorAll("[data-askq-close]");
  const backdrop =
    modal.querySelector('[data-askq-close].absolute') ||
    modal.querySelector("div.absolute");

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

  // ---------- Блокировка скролла страницы при открытой модалке ----------
  const scrollLock = {
    y: 0,
    lock() {
      // Запоминаем текущую позицию страницы
      this.y = window.scrollY || 0;

      // Фиксируем body, чтобы страница не прокручивалась
      document.body.style.position = "fixed";
      document.body.style.top = `-${this.y}px`;
      document.body.style.left = "0";
      document.body.style.right = "0";
      document.body.style.width = "100%";
    },
    unlock() {
      // Возвращаем стили body обратно и докручиваем к исходной позиции
      const y = this.y || 0;
      document.body.style.position = "";
      document.body.style.top = "";
      document.body.style.left = "";
      document.body.style.right = "";
      document.body.style.width = "";
      window.scrollTo(0, y);
    },
  };

  // ---------- Открытие/закрытие модального окна ----------
  function onEsc(e) {
    // Закрываем по Escape
    if (e.key === "Escape") closeModal();
  }

  function openModal() {
    // Показываем модалку
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");

    // Плавная анимация появления (бекдроп + диалог)
    requestAnimationFrame(() => {
      backdrop?.classList.remove("opacity-0");
      backdrop?.classList.add("opacity-100");
      dialog.classList.remove("opacity-0", "translate-y-2");
      dialog.classList.add("opacity-100", "translate-y-0");
    });

    // Перед открытием очищаем ошибки и фокусируем первое поле
    clearErrors();
    const first = form.querySelector('input[name="name"]');
    setTimeout(() => first?.focus(), 60);

    // Блокируем скролл и вешаем Escape
    scrollLock.lock();
    document.addEventListener("keydown", onEsc);
  }

  function closeModal() {
    // Анимация скрытия (бекдроп + диалог)
    backdrop?.classList.remove("opacity-100");
    backdrop?.classList.add("opacity-0");
    dialog.classList.remove("opacity-100", "translate-y-0");
    dialog.classList.add("opacity-0", "translate-y-2");

    // После анимации — скрываем модалку полностью
    setTimeout(() => {
      modal.classList.add("hidden");
      modal.setAttribute("aria-hidden", "true");
    }, 200);

    // Снимаем обработчики и возвращаем скролл
    document.removeEventListener("keydown", onEsc);
    scrollLock.unlock();
  }

  // ✅ Кнопки-открыватели: запрещаем навигацию и всплытие событий (CAPTURE!)
  openers.forEach((btn) => {
    btn.addEventListener(
      "click",
      (e) => {
        e.preventDefault();
        e.stopPropagation();
        openModal();
      },
      true
    );
  });

  // Кнопки-закрыватели
  closers.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeModal();
    });
  });

  // Клик по затемнению (backdrop) закрывает модалку
  if (backdrop) {
    backdrop.addEventListener(
      "click",
      (e) => {
        e.preventDefault();
        e.stopPropagation();
        closeModal();
      },
      true
    );
  }

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
  const nfBox = () => form.querySelector("[data-nf]");

  function clearErrors() {
    // Скрываем ошибки конкретных полей
    form.querySelectorAll("[data-err]").forEach((el) => {
      el.classList.add("hidden");
      el.textContent = "";
    });

    // Скрываем “общую” ошибку формы (non-field error)
    const nf = nfBox();
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
    // Показываем общую ошибку формы
    const nf = nfBox();
    if (!nf) return;
    nf.textContent = text;
    nf.classList.remove("hidden");
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

  // ---------- Парсинг ошибок Django из HTML-ответа (contacts/ask_question.html) ----------
  function parseErrorsFromHtml(htmlText) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, "text/html");

    // Пытаемся вытащить текст ошибки из “ожидаемых” контейнеров
    const pick = (fieldName) => {
      const el =
        doc.querySelector(`#error-${fieldName}`) ||
        doc.querySelector(`[data-error-for="${fieldName}"]`);

      if (!el) return "";

      const li = el.querySelector("li");
      if (li) return li.textContent.trim();

      return el.textContent.trim();
    };

    const errors = {
      name: pick("name"),
      contact: pick("contact"),
      question: pick("question"),
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

    // Запасной вариант: стандартные Django errorlist рядом с полями
    if (!errors.name || !errors.contact || !errors.question) {
      doc.querySelectorAll("ul.errorlist").forEach((ul) => {
        const text = ul.textContent.trim();
        if (!text) return;

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
    Object.keys(errors).forEach((k) => {
      errors[k] = (errors[k] || "").trim();
    });

    return errors;
  }

  function smoothHideForm() {
    // Плавно “прячем” тело формы при успешной отправке
    const body = document.getElementById("askq-form-body");
    if (!body) return;
    body.classList.add(
      "transition-all",
      "duration-200",
      "opacity-0",
      "translate-y-1"
    );
  }

  // ---------- Отправка формы (fetch) ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    clearErrors();

    // Лёгкая фронт-валидация (для UX, серверная всё равно остаётся обязательной)
    const name = (form.querySelector('input[name="name"]')?.value || "").trim();
    const contact = (
      form.querySelector('input[name="contact"]')?.value || ""
    ).trim();
    const question = (
      form.querySelector('textarea[name="question"]')?.value || ""
    ).trim();

    let hasErr = false;

    if (name.length < 2) {
      showFieldError("name", "Введите имя (минимум 2 символа).");
      hasErr = true;
    }
    if (contact.length < 5) {
      showFieldError("contact", "Укажите телефон или email.");
      hasErr = true;
    }
    if (question.length < 5) {
      showFieldError("question", "Опишите вопрос (минимум 5 символов).");
      hasErr = true;
    }

    if (hasErr) {
      toast("Проверьте поля формы.", "error");
      return;
    }

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
        toast("Вопрос отправлен! Мы скоро ответим.", "success");

        setTimeout(() => {
          // Сбрасываем форму и закрываем модалку
          form.reset();
          const body = document.getElementById("askq-form-body");
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

      ["name", "contact", "question"].forEach((field) => {
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