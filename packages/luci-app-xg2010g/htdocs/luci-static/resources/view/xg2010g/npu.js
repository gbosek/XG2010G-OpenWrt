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
      E('p', {}, _('Read-only Test-4B verification view for the Airoha NPU, PPE, QDMA and flow-offload datapath. It shows nft flowtables, tc offload state and per-interface Airoha/RMON statistics.')),
      E('p', {}, _('Runtime acceptance requires two snapshots while routed iperf3 traffic is running: PPE/FOE/QDMA/GDM counters must increase consistently with active flow offload. A page that merely loads, or an NPU firmware message by itself, is not considered proof of hardware offload.')),
      E('pre', { 'style': 'white-space:pre-wrap' }, [ data || _('No data') ])
    ]);
  },

  handleSaveApply: null,
  handleSave: null,
  handleReset: null
});
