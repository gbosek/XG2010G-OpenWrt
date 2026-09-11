'use strict';
'require view';
'require form';
'require fs';
'require ui';
'require uci';

function runPon(args) {
  return fs.exec_direct('/usr/libexec/xg2010g-pon', args || []).catch(function(err) {
    return _('PON action failed: %s').format(err.message || err);
  });
}

function notifyResult(title, text) {
  ui.addNotification(null, E('p', {}, [ title ]));
  var box = document.getElementById('xg2010g-pon-runtime');
  if (box)
    box.textContent = text || _('No output');
}

return view.extend({
  load: function() {
    return Promise.all([
      uci.load('pon'),
      runPon([ 'status' ])
    ]);
  },

  render: function(data) {
    var m, s, o;
    var status = data[1] || _('No runtime data');

    m = new form.Map('pon', _('XG2010G PON'),
      _('Functional PON management for the XG2010G. Values are written to /etc/config/pon and applied to ponctl, OMCI or OAM through the base-firmware backend.'));

    s = m.section(form.NamedSection, 'line0', 'xpon', _('Line / PLOAM identity'));
    s.addremove = false;

    o = s.option(form.Value, 'device', _('PON device'));
    o.default = 'pon0';
    o.rmempty = false;

    o = s.option(form.ListValue, 'mode', _('PON mode'));
    o.value('', _('Driver default'));
    o.value('gpon', 'GPON');
    o.value('xgpon', 'XG-PON');
    o.value('xgspon', 'XGS-PON');
    o.value('epon-1g', 'EPON 1G');
    o.value('epon-10g-1g', '10G-EPON 10G/1G');
    o.value('epon-10g-10g', '10G-EPON 10G/10G');
    o.default = '';
    o.rmempty = true;

    o = s.option(form.Value, 'serial_number', _('PLOAM Serial Number'));
    o.placeholder = 'VEND12345678';
    o.description = _('Leave empty to use the board/NVMEM identity. Accepts 16 raw hex digits or 4-character Vendor ID + 8 hex digits.');
    o.rmempty = true;

    o = s.option(form.Value, 'registration_id', _('Registration ID'));
    o.placeholder = 'text:your-registration-id';
    o.description = _('Use text:... up to 36 UTF-8 bytes, or hex: followed by exactly 72 hexadecimal digits. Leave empty for the standard all-zero default.');
    o.rmempty = true;

    s = m.section(form.NamedSection, 'line0_omci', 'omci', _('OMCI identity'));
    s.addremove = false;

    [
      [ 'device', _('OMCI device'), 'omci0' ],
      [ 'vendor_id', _('Vendor ID'), '' ],
      [ 'equipment_id', _('Equipment ID'), '' ],
      [ 'hardware_version', _('Hardware version'), '' ],
      [ 'software_version', _('Software version'), '' ],
      [ 'operator_id', _('Operator ID'), '' ],
      [ 'loid', _('LOID'), '' ]
    ].forEach(function(v) {
      var x = s.option(form.Value, v[0], v[1]);
      if (v[2]) x.default = v[2];
      x.rmempty = (v[0] !== 'device');
    });

    o = s.option(form.Value, 'loid_password', _('LOID password'));
    o.password = true;
    o.rmempty = true;

    s = m.section(form.NamedSection, 'line0_oam', 'oam', _('EPON OAM identity'));
    s.addremove = false;

    o = s.option(form.Value, 'device', _('OAM device'));
    o.default = 'oam0';
    o.rmempty = false;

    o = s.option(form.ListValue, 'operator', _('OAM profile'));
    o.value('ctc', 'CTC');
    o.value('ieee', 'IEEE 802.3ah');
    o.default = 'ctc';

    [
      [ 'ctc_oui', _('CTC OUI'), '111111' ],
      [ 'ctc_versions', _('CTC versions'), '21 30' ],
      [ 'vendor_id', _('Vendor ID'), '' ],
      [ 'model', _('Model'), '' ],
      [ 'equipment_id', _('Equipment ID'), '' ],
      [ 'hardware_version', _('Hardware version'), '' ],
      [ 'software_version', _('Software version'), '' ],
      [ 'firmware_version', _('Firmware version'), '' ],
      [ 'chipset_id', _('Chipset ID'), '' ],
      [ 'loid', _('LOID'), '' ],
      [ 'ge_ports', _('GE ports'), '1' ]
    ].forEach(function(v) {
      var x = s.option(form.Value, v[0], v[1]);
      if (v[2]) x.default = v[2];
      x.rmempty = true;
    });

    o = s.option(form.Value, 'loid_password', _('LOID password'));
    o.password = true;
    o.rmempty = true;

    return m.render().then(function(mapNode) {
      var applyBtn = E('button', {
        'class': 'btn cbi-button-action important',
        'click': ui.createHandlerFn(this, function() {
          return m.save().then(function() {
            return uci.save().then(function() {
              return runPon([ 'apply' ]).then(function(out) {
                notifyResult(_('PON configuration applied'), out);
              });
            });
          });
        })
      }, [ _('Save and apply PON') ]);

      var restartBtn = E('button', {
        'class': 'btn cbi-button-action',
        'click': ui.createHandlerFn(this, function() {
          return runPon([ 'restart' ]).then(function(out) {
            notifyResult(_('PON services restarted'), out);
          });
        })
      }, [ _('Restart PON / OMCI / OAM') ]);

      var refreshBtn = E('button', {
        'class': 'btn',
        'click': ui.createHandlerFn(this, function() {
          return runPon([ 'status' ]).then(function(out) {
            notifyResult(_('Runtime status refreshed'), out);
          });
        })
      }, [ _('Refresh runtime status') ]);

      var waitBtn = E('button', {
        'class': 'btn',
        'click': ui.createHandlerFn(this, function() {
          return runPon([ 'wait-o5', '60' ]).then(function(out) {
            notifyResult(_('O5 wait completed'), out);
          });
        })
      }, [ _('Wait for O5 (60 s)') ]);

      var alloc = E('input', { 'id': 'xg2010g-alloc-id', 'class': 'cbi-input-text', 'placeholder': 'ALLOC-ID' });
      var gem = E('input', { 'id': 'xg2010g-gem-id', 'class': 'cbi-input-text', 'placeholder': 'GEM-ID' });
      var dpSet = E('button', {
        'class': 'btn cbi-button-action',
        'click': ui.createHandlerFn(this, function() {
          return runPon([ 'datapath-set', alloc.value, gem.value ]).then(function(out) {
            notifyResult(_('PON data path updated'), out);
          });
        })
      }, [ _('Set Alloc-ID / GEM-ID') ]);
      var dpClear = E('button', {
        'class': 'btn cbi-button-negative',
        'click': ui.createHandlerFn(this, function() {
          return runPon([ 'datapath-clear' ]).then(function(out) {
            notifyResult(_('PON data path cleared'), out);
          });
        })
      }, [ _('Clear data path') ]);

      return E([], [
        mapNode,
        E('div', { 'class': 'cbi-page-actions' }, [ applyBtn, ' ', restartBtn, ' ', refreshBtn, ' ', waitBtn ]),
        E('h3', {}, [ _('Data Path') ]),
        E('p', {}, [ _('Directly controls ponctl data-path for the configured PON device.') ]),
        E('div', { 'class': 'cbi-page-actions' }, [ alloc, ' ', gem, ' ', dpSet, ' ', dpClear ]),
        E('h3', {}, [ _('Runtime status') ]),
        E('pre', { 'id': 'xg2010g-pon-runtime', 'style': 'white-space:pre-wrap' }, [ status ])
      ]);
    }.bind(this));
  },

  handleSaveApply: null,
  handleSave: null,
  handleReset: null
});
