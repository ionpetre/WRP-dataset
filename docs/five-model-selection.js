/* Browser data for the shared five-cluster model. */
(() => {
  'use strict';
  const report = window.WRP_SHARED_FIVE;
  if (report) {
    window.WRP_WAVE_DATA = {
      models: report.models,
      overlap: report.overlap,
      point: report.point,
      stability: report.stability,
      shares: { full: report.shares },
      reference: { full: report.reference }
    };
  }
  const country = window.WRP_SHARED_FIVE_COUNTRIES;
  if (country) {
    window.WRP_COUNTRY_WAVES = {
      models: country.models,
      references: { full: country.reference }
    };
  }
})();
