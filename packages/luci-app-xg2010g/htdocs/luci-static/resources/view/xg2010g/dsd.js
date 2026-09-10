'use strict';
'require view';
'require fs';
'require ui';

return view.extend({
  load: function() {
    return fs.exec_direct('/usr/libexec/xg2010g-dsd', [ 'status' ]).catch(function(err) {
      return _('Unable to read DSD status: %s').format(err.message || err);
    });
  },

  render: function(data) {
    var out = E('pre', { 'style': 'white-space:pre-wrap' }, [ data || _('No data') ]);
    var run = function(args) {
      ui.showModal(_('XG2010G DSD'), [ E('p', { 'class': 'spinning' }, _('Working…')) ]);
      fs.exec_direct('/usr/libexec/xg2010g-dsd', args).then(function(txt) {
        ui.showModal(_('XG2010G DSD'), [ E('pre', { 'style': 'white-space:pre-wrap' }, [ txt ]), E('div', { 'class': 'right' }, [ E('button', { 'class': 'btn', 'click': ui.hideModal }, _('Close')) ]) ]);
      }).catch(function(err) {
        ui.addNotification(null, E('p', {}, err.message || err), 'error');
        ui.hideModal();
      });
    };

    return E([], [
      E('h2', {}, _('XG2010G DSD / Calibration')),
      E('p', {}, _('Test-4B safety mode: backup, inspect and extract the original DSD calibration window. NAND write/import is intentionally disabled until the base-firmware LAN fixes pass real-hardware validation.')),
      out,
      E('div', { 'class': 'cbi-page-actions' }, [
        E('button', { 'class': 'btn cbi-button-action', 'click': function() { run([ 'backup' ]); } }, _('Backup DSD to /tmp')),
        ' ',
        E('button', { 'class': 'btn', 'click': function() { run([ 'check', '/tmp/xg2010g-dsd.bin' ]); } }, _('Validate staged DSD')),
        ' ',
        E('button', { 'class': 'btn', 'click': function() { run([ 'extract', '/tmp/xg2010g-dsd.bin' ]); } }, _('Extract 512-byte calibration'))
      ]),
      E('p', {}, _('For this test build, stage a DSD backup as /tmp/xg2010g-dsd.bin (for example with SCP) before using Validate/Extract. Browser upload and flash-write controls will be enabled only after validation rules are proven.'))
    ]);
  },

  handleSaveApply: null,
  handleSave: null,
  handleReset: null
});
