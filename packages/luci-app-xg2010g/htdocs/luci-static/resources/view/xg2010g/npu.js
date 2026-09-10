'use strict';
'require view';
'require fs';

return view.extend({
  load: function() {
    return fs.exec_direct('/usr/libexec/xg2010g-status', [ 'npu' ]).catch(function(err) {
      return _('Unable to read NPU diagnostics: %s').format(err.message || err);
    });
  },

  render: function(data) {
    return E([], [
      E('h2', {}, _('XG2010G NPU / PPE / QDMA')),
      E('p', {}, _('Read-only Test-3 diagnostics for NPU, PPE, QDMA and flow offload. Writable controls will be added only after the real driver interfaces are verified.')),
      E('pre', { 'style': 'white-space:pre-wrap' }, [ data || _('No data') ])
    ]);
  },

  handleSaveApply: null,
  handleSave: null,
  handleReset: null
});
