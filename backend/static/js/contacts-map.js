(function () {
  function qs(id) { return document.getElementById(id); }

  const mapEl = qs("ymap");
  const routeBtn = qs("route-btn");

  if (!mapEl) return;

  // helper для кнопки
  function setRouteEnabled(enabled) {
    if (!routeBtn) return;
    routeBtn.disabled = !enabled;

    routeBtn.classList.toggle("bg-gray-300", !enabled);
    routeBtn.classList.toggle("text-gray-500", !enabled);
    routeBtn.classList.toggle("cursor-not-allowed", !enabled);

    routeBtn.classList.toggle("bg-blue-600", enabled);
    routeBtn.classList.toggle("hover:bg-blue-700", enabled);
    routeBtn.classList.toggle("text-white", enabled);
    routeBtn.classList.toggle("cursor-pointer", enabled);
  }

  // ждём, пока ymaps реально загрузится
  function waitYmapsReady(cb) {
    const t0 = Date.now();
    (function check() {
      if (window.ymaps && typeof window.ymaps.ready === "function") {
        window.ymaps.ready(cb);
        return;
      }
      if (Date.now() - t0 > 15000) {
        console.error("YMaps not loaded (timeout). Check API key / script include.");
        return;
      }
      setTimeout(check, 100);
    })();
  }

  const cfg = window.CONTACTS_MAP || {};
  const address = (cfg.address || "").trim();
  const title = cfg.title || "Mediscan";

  // Если координаты заданы — используем их, это надежнее геокодинга.
  // ВАЖНО: Yandex coords = [lon, lat]
  // Можно передавать либо cfg.coords = [37.56, 55.73], либо как у тебя: руками ниже.
  const fallbackCoords = [37.562577, 55.737497]; // <-- FIX: порядок [lon, lat]
  const presetCoords = Array.isArray(cfg.coords) && cfg.coords.length === 2
    ? cfg.coords
    : fallbackCoords;

  setRouteEnabled(false);

  waitYmapsReady(async function init() {
    if (!address && !presetCoords) {
      console.error("CONTACTS_MAP.address is empty and coords not provided");
      return;
    }

    // 1) создаём карту (центр сразу правильный)
    const map = new ymaps.Map(mapEl, {
      center: presetCoords,       // <-- FIX
      zoom: 16,
      controls: []
    }, {
      suppressMapOpenBlock: true
    });

    // добавим только +/-
    map.controls.add("zoomControl", { position: { right: 14, top: 90 } });

    // 2) получаем coords: либо из cfg.coords, либо геокодингом
    let coords = presetCoords;

    // Геокодим ТОЛЬКО если координаты не переданы явно
    // (и чтобы не уехать на "примерную" точку по адресу)
    const shouldGeocode = !(Array.isArray(cfg.coords) && cfg.coords.length === 2);

    if (shouldGeocode) {
      try {
        const res = await ymaps.geocode(address, { results: 1 });
        const geoObj = res.geoObjects.get(0);

        if (!geoObj) {
          console.error("Geocode: address not found:", address);
          // остаёмся на fallbackCoords
        } else {
          coords = geoObj.geometry.getCoordinates(); // уже [lon, lat]
        }
      } catch (e) {
        console.error("Geocode failed:", e);
        // остаёмся на fallbackCoords
      }
    }

    // 3) ставим маркер
    map.setCenter(coords, 16, { duration: 250 });

    const placemark = new ymaps.Placemark(
      coords,
      {
        iconCaption: title,
        balloonContent: address
          ? `<b>${title}</b><br>${address}`
          : `<b>${title}</b>`
      },
      {
        preset: "islands#blueDotIconWithCaption",
        openBalloonOnClick: true
      }
    );

    map.geoObjects.add(placemark);

    // 4) кнопка "Построить маршрут"
    setRouteEnabled(true);

    let currentRoute = null;

    if (routeBtn) {
      routeBtn.addEventListener("click", async () => {
        setRouteEnabled(false);

        try {
          const geo = await ymaps.geolocation.get({
            provider: "auto",
            mapStateAutoApply: false
          });

          // Иногда position может быть undefined — берём координаты из геообъекта
          const userCoords =
            geo.geoObjects.position ||
            (geo.geoObjects.get(0) && geo.geoObjects.get(0).geometry.getCoordinates());

          if (!userCoords) {
            throw new Error("User coords not detected");
          }

          const route = new ymaps.multiRouter.MultiRoute(
            {
              referencePoints: [userCoords, coords],
              params: { routingMode: "auto" }
            },
            {
              boundsAutoApply: true,
              wayPointVisible: false,
              viaPointVisible: false,
              routeActiveStrokeWidth: 6,
              routeActiveStrokeColor: "#2563eb"
            }
          );

          // удаляем предыдущий маршрут (если был), маркер не трогаем
          if (currentRoute) {
            map.geoObjects.remove(currentRoute);
            currentRoute = null;
          }

          map.geoObjects.add(route);
          currentRoute = route;

        } catch (e) {
          console.error("Route build failed:", e);
          alert("Не удалось получить геолокацию или построить маршрут. Разрешите доступ к геопозиции.");
        } finally {
          setRouteEnabled(true);
        }
      });
    }
  });
})();


