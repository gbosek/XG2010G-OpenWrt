'use strict';
'require view';
'require fs';
'require ui';

return view.extend({
  load: function() {
    return fs.exec_direct('/usr/libexec/xg2010g-status', [ 'pon' ]).catch(function(err) {
      return _('Unable to read PON diagnostics: %s').format(err.message || err);
    });
  },

  render: function(data) {
    return E([], [
      E('h2', {}, _('XG2010G PON')),
      E('p', {}, _('Read-only Test-3 diagnostics. Configuration controls will only be enabled after the 6.18 PON interfaces are verified on real hardware.')),
      E('pre', { 'style': 'white-space:pre-wrap' }, [ data || _('No data') ])
    ]);
  },

  handleSaveApply: null,
  handleSave: null,
  handleReset: null
});
