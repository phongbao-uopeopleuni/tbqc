/**
 * Panzoom (@panzoom/panzoom) — zoom lăn chuột, pinch mobile, pan mượt cho .tree trong #treeContainer.
 * Tải từ CDN trước file này. Không có Panzoom thì family-tree-ui.js dùng transform + kéo tay như cũ.
 */
(function () {
  var treePanzoomInstance = null;
  var wheelParent = null;
  var wheelHandler = null;
  var changeHandler = null;
  var treeDivForPanzoom = null;

  function destroyTreePanzoom() {
    if (treePanzoomInstance) {
      if (!window.__treePanzoomNoPreserveSnapshot) {
        try {
          window.__treePanzoomSnapshot = {
            scale: treePanzoomInstance.getScale(),
            x: treePanzoomInstance.getPan().x,
            y: treePanzoomInstance.getPan().y
          };
        } catch (e) {
          window.__treePanzoomSnapshot = null;
        }
      }
      if (treeDivForPanzoom && changeHandler) {
        try {
          treeDivForPanzoom.removeEventListener('panzoomchange', changeHandler);
        } catch (e2) { /* ignore */ }
      }
      changeHandler = null;
      treeDivForPanzoom = null;
      try {
        treePanzoomInstance.destroy();
      } catch (e3) { /* ignore */ }
      treePanzoomInstance = null;
    }
    if (wheelParent && wheelHandler) {
      wheelParent.removeEventListener('wheel', wheelHandler);
      wheelParent = null;
      wheelHandler = null;
    }
    if (typeof window !== 'undefined') {
      window.treePanzoomInstance = null;
    }
  }

  /**
   * Gắn Panzoom lên treeDiv (đã append vào #treeContainer).
   * @returns {boolean} true nếu đã gắn
   */
  function initTreePanzoom(treeDiv) {
    if (typeof Panzoom === 'undefined' || !treeDiv) {
      return false;
    }

    var snap = window.__treePanzoomSnapshot;
    window.__treePanzoomSnapshot = null;

    /* Cây gia phả rộng hàng chục nghìn px — cần zoom-out sâu hơn 0.05 để “Vừa khung” thật sự thấy toàn cây */
    /* Cây cực rộng: zoom-out sâu hơn để “Vừa khung” / xem toàn bộ */
    var minScale = 0.004;
    if (typeof window !== 'undefined') {
      window.treePanzoomMinScale = minScale;
    }

    var opts = {
      maxScale: 2,
      minScale: minScale,
      step: 0.1,
      canvas: true,
      excludeClass: 'panzoom-exclude',
      // 1 = tỷ lệ đọc được trước khi fitTreeToView chạy; tránh màn hình trắng khi fit bị bỏ qua (khung 0×0 khi cổng ẩn).
      startScale: snap ? snap.scale : 1,
      startX: snap ? snap.x : 0,
      startY: snap ? snap.y : 0
    };

    try {
      treePanzoomInstance = Panzoom(treeDiv, opts);
    } catch (err) {
      console.warn('[TreePanzoom] Panzoom init failed:', err);
      return false;
    }

    /* GIỮ transform-origin = 50% 50% (Panzoom canvas:true ngầm hiểu như vậy cho zoomIn/zoomOut/focal).
       Mọi công thức pan ở family-tree-ui.js đã được cập nhật theo công thức origin-center. */
    treeDivForPanzoom = treeDiv;
    changeHandler = function () {
      if (typeof window !== 'undefined' && typeof window.syncFamilyTreeZoomFromPanzoom === 'function') {
        window.syncFamilyTreeZoomFromPanzoom();
      }
    };
    treeDiv.addEventListener('panzoomchange', changeHandler);

    var markExcluded = function () {
      treeDiv.querySelectorAll('.node, .family-node, .connector, .connector-junction').forEach(function (el) {
        el.classList.add('panzoom-exclude');
      });
    };
    markExcluded();

    wheelParent = document.querySelector('.tree-container-wrapper') || document.getElementById('treeContainer');
    if (wheelParent && treePanzoomInstance.zoomWithWheel) {
      /* Panzoom.zoomWithWheel dùng focal nội bộ — kết hợp pan pre-scale hàng trăm ngàn px gây NaN → mất render.
         Tự tính scale mới và uỷ thác zoomAroundWheel (bên family-tree-ui.js) để giữ điểm chuột cố định. */
      wheelHandler = function (ev) {
        ev.preventDefault();
        if (typeof window.zoomAroundPointer === 'function' && typeof window.treePanzoomInstance !== 'undefined' && window.treePanzoomInstance) {
          var pz = window.treePanzoomInstance;
          var cur = pz.getScale();
          var factor = ev.deltaY < 0 ? 1.15 : 1 / 1.15;
          var target = cur * factor;
          var zmin = typeof window.treePanzoomMinScale === 'number' ? window.treePanzoomMinScale : 0.004;
          target = Math.max(zmin, Math.min(2, target));
          window.zoomAroundPointer(target, ev.clientX, ev.clientY);
          return;
        }
        treePanzoomInstance.zoomWithWheel(ev);
      };
      wheelParent.addEventListener('wheel', wheelHandler, { passive: false });
    }

    if (typeof window !== 'undefined') {
      window.treePanzoomInstance = treePanzoomInstance;
      if (typeof window.syncFamilyTreeZoomFromPanzoom === 'function') {
        window.syncFamilyTreeZoomFromPanzoom();
      }
    }

    if (snap) {
      window.__skipNextTreeFit = true;
    }

    return true;
  }

  function clearTreePanzoomSnapshot() {
    window.__treePanzoomSnapshot = null;
  }

  if (typeof window !== 'undefined') {
    window.destroyTreePanzoom = destroyTreePanzoom;
    window.initTreePanzoom = initTreePanzoom;
    window.clearTreePanzoomSnapshot = clearTreePanzoomSnapshot;
  }
})();
