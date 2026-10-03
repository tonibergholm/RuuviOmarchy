const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const model = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../Model.js'),'utf8'),model);
test('favorite default, explicit selection and filtering',()=>{
  const sensors=[{id:'aa',favorite:false},{id:'bb',favorite:true}];
  assert.equal(model.primary(sensors,'').id,'bb');
  assert.equal(model.primary(sensors,'AA').id,'aa');
  assert.equal(model.primary(sensors,'missing'),null);
  assert.equal(model.primary([],''),null);
  assert.equal(model.rows({sensors},true).length,1);
  assert.equal(model.rows(null,false).length,0);
});
test('units, unavailable values, safe metric and stale ages',()=>{
  assert.equal(model.value(-2.4,'temperature'),'-2.4°C');
  assert.equal(model.value(1001.25,'pressure'),'1001.3 hPa');
  assert.equal(model.value(null,'humidity'),'—');
  assert.equal(model.value(Infinity,'temperature'),'—');
  assert.equal(model.metric('bogus'),'temperature');
  assert.equal(model.age(90),'1m ago');
  assert.equal(model.age(90000),'1d ago');
});
