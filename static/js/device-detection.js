/**
 * Device Detection Utility
 * Phát hiện loại thiết bị và trả về mode phù hợp
 */
(function() {
  'use strict';
  
  const DeviceDetection = {
    // Detect device type
    detectDevice: function() {
      const width = window.innerWidth;
      const userAgent = navigator.userAgent || navigator.vendor || window.opera;
      
      // Mobile detection
      const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase()) 
        || width <= 768;
      
      // Tablet detection
      const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent.toLowerCase())
        || (width > 768 && width <= 1024);
      
      // Desktop detection
      const isDesktop = width > 1024;
      
      // Touch device detection
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      
      return {
        isMobile: isMobile,
        isTablet: isTablet,
        isDesktop: isDesktop,
        isTouchDevice: isTouchDevice,
        width: width,
        height: window.innerHeight,
        userAgent: userAgent,
        mode: isMobile ? 'mobile' : (isTablet ? 'tablet' : 'desktop')
      };
    },
    
    // Add device class to body
    addDeviceClass: function() {
      const device = this.detectDevice();
      const body = document.body;
      
      // Remove existing classes
      body.classList.remove('device-mobile', 'device-tablet', 'device-desktop', 'device-touch');
      
      // Add new classes
      body.classList.add(`device-${device.mode}`);
      if (device.isTouchDevice) {
        body.classList.add('device-touch');
      }
      
      // Add data attribute
      body.setAttribute('data-device-mode', device.mode);
      body.setAttribute('data-device-width', device.width);
      
      return device;
    },
    
    // Initialize on load and resize
    init: function() {
      // Run immediately
      this.addDeviceClass();
      
      // Run on resize (debounced)
      let resizeTimer;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          this.addDeviceClass();
          // Dispatch custom event
          window.dispatchEvent(new CustomEvent('deviceModeChanged', {
            detail: this.detectDevice()
          }));
        }, 250);
      });
      
      // Run on orientation change
      window.addEventListener('orientationchange', () => {
        setTimeout(() => {
          this.addDeviceClass();
        }, 100);
      });
    }
  };
  
  // Auto-initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => DeviceDetection.init());
  } else {
    DeviceDetection.init();
  }
  
  // Export to window
  window.DeviceDetection = DeviceDetection;
})();
