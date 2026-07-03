# BackendMods.md

## Hotfix: PHP 8.x Restler Validator crash on union types

**File**: `/var/www/html/includes/restler/framework/Luracast/Restler/Data/Validator.php` (inside `dolibarr-app` container)

**Reason**: PHP 8.x throws `TypeError: Illegal offset type in isset or empty` when a non-string/non-int value is used as an array key in `isset()`. The Restler framework's PHPDoc parser produces a non-scalar `$info->type` for union types like `datetime|string` (e.g., `api_tasks.class.php:654` `@param datetime|string $date`), causing `isset(static::$preFilters[$info->type])` to crash on line 427.

**Before**:
```php
isset(static::$preFilters[$info->type]) &&
```

**After**:
```php
isset(static::$preFilters[(string)$info->type]) &&
```

**Applied via**:
```bash
docker exec dolibarr-app sed -i 's|isset(static::\$preFilters\[\$info->type\])|isset(static::\$preFilters[(string)\$info->type])|' /var/www/html/includes/restler/framework/Luracast/Restler/Data/Validator.php
```

## Hotfix: PHP `!(-1)` bug in API user delete check

**File**: `/var/www/html/user/class/api_users.class.php` (inside `dolibarr-app` container)

**Reason**: `User::delete()` returns `1` on success and `-1` on error (rollback). The API handler checked `if (!$this->useraccount->delete(...))` which evaluates `!(-1)` as `false` (because `-1` is truthy in PHP), so the error was silently swallowed and the handler returned a success response even when the user was NOT deleted.

**Before**:
```php
if (!$this->useraccount->delete(DolibarrApiAccess::$user)) {
```

**After**:
```php
if ($this->useraccount->delete(DolibarrApiAccess::$user) < 0) {
```

**Note**: This fix exposes the underlying `USER_DELETE` trigger failure in `user.class.php:1834`, which causes the delete to rollback. C4 delete_users now correctly reports FAILED instead of a false PASS.

**Applied via**:
```bash
docker exec dolibarr-app sed -i 's|if (!$this->useraccount->delete(DolibarrApiAccess::$user))|if ($this->useraccount->delete(DolibarrApiAccess::$user) < 0)|' /var/www/html/user/class/api_users.class.php
```

## Hotfix: Warehouse PUT/DELETE missing `$dbtablename` in access check

**File**: `/var/www/html/product/stock/class/api_warehouses.class.php` (inside `dolibarr-app` container)

**Reason**: `_checkAccessToResource('stock', $this->warehouse->id)` was called without the 3rd argument `'entrepot'` (the database table name) in both the `put()` and `delete()` handlers. The GET handler correctly passes `'entrepot'`. Without the table name, `checkUserAccessToObject()` cannot find the correct DB table for the ownership SQL query and returns false for every warehouse, causing a 403 Forbidden on every PUT/DELETE regardless of permissions.

**Before** (lines 279, 349):
```php
if (!DolibarrApi::_checkAccessToResource('stock', $this->warehouse->id)) {
```

**After**:
```php
if (!DolibarrApi::_checkAccessToResource('stock', $this->warehouse->id, 'entrepot')) {
```

**Applied via**:
```bash
docker exec dolibarr-app sed -i 's|if (!DolibarrApi::_checkAccessToResource('\''stock'\'', $this->warehouse->id)) {|if (!DolibarrApi::_checkAccessToResource('\''stock'\'', $this->warehouse->id, '\''entrepot'\'')) {|g' /var/www/html/product/stock/class/api_warehouses.class.php
```

## Hotfix: Thirdparty representatives GET — access check before fetch + wrong fetch return check

**File**: `/var/www/html/societe/class/api_thirdparties.class.php` (inside `dolibarr-app` container)

**Reason**: Two bugs in `getSalesRepresentatives()`:

1. `_checkAccessToResource('societe', $id)` was called **before** `$this->company->fetch($id)`, using the raw `$id` parameter instead of the loaded object's `$this->company->id`. All other thirdparty handlers (POST/DELETE representatives, update, delete) correctly fetch first then check using `$this->company->id`.

2. The fetch result was checked with `if (!is_array($result))` but `Societe::fetch()` returns an integer (`1` on success, `0` or `-1` on failure), not an array. So success was always treated as "not found". Other functions use the correct `if (!$result)` check.

**Before**:
```php
$result = $this->company->fetch($id);
if (!is_array($result)) {
    throw new RestException(404, 'Thirdparty not found');
}
```

**After**:
```php
$result = $this->company->fetch($id);
if (!$result) {
    throw new RestException(404, 'Thirdparty not found');
}
if (!DolibarrApi::_checkAccessToResource('societe', $this->company->id)) {
    throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
}
```

**Applied via** (copy file out, fix with Python, copy back):
```bash
# The fix involved multiple regex operations; final state verified via `docker cp` and Python
docker cp dolibarr-app:/var/www/html/societe/class/api_thirdparties.class.php /tmp/
# Python: replace "if (!is_array($result))" with "if (!$result)" in getSalesRepresentatives
# Python: move _checkAccessToResource after fetch, use $this->company->id
docker cp /tmp/api_thirdparties.class.php dolibarr-app:/var/www/html/societe/class/api_thirdparties.class.php
```

## Hotfix: Workstations missing POST/PUT/DELETE handlers

**File**: `/var/www/html/workstation/class/api_workstations.class.php` (inside `dolibarr-app` container)

**Reason**: The `Workstations` API class only had `get()`, `getByRef()`, and `index()` methods. No `post()`, `put()`, or `delete()` handlers existed, so POST/PUT/DELETE returned 404. The `Workstation` model class has `create()`, `update()`, and `delete()` methods, so adding the API handlers was straightforward.

**Permission checks** (matching DB right defs: `module=workstation, perms=workstation`):
- POST/PUT: `$user->rights->workstation->workstation->write`
- DELETE: `$user->rights->workstation->workstation->delete`

**Note**: The workstation module's permission subperms use English names (`read`, `write`, `delete`) rather than French (`lire`, `creer`, `supprimer`). The admin user (aeinstein, user 1) requires these rights to be explicitly granted in `llx_user_rights`.

**Added: `post()`** — creates a workstation, returns `$this->get($id)`:
```php
public function post($request_data = null)
{
    if (!DolibarrApiAccess::$user->rights->workstation->workstation->write) {
        throw new RestException(403);
    }
    foreach ($request_data as $field => $value) {
        if ($field === 'caller') {
            $this->workstation->context['caller'] = sanitizeVal($request_data['caller'], 'aZ09');
            continue;
        }
        if ($field == 'array_options' && is_array($value)) {
            foreach ($value as $index => $val) {
                $this->workstation->array_options[$index] = $this->_checkValForAPI('extrafields', $val, $this->workstation);
            }
            continue;
        }
        $this->workstation->$field = $this->_checkValForAPI($field, $value, $this->workstation);
    }
    $id = $this->workstation->create(DolibarrApiAccess::$user);
    if ($id > 0) {
        return $this->get($id);
    } else {
        throw new RestException(500, $this->workstation->error);
    }
}
```

**Added: `put()`** — updates a workstation, returns `$this->get($id)`:
```php
public function put($id, $request_data = null)
{
    if (!DolibarrApiAccess::$user->rights->workstation->workstation->write) {
        throw new RestException(403);
    }
    $result = $this->workstation->fetch($id);
    if (!$result) {
        throw new RestException(404, 'Workstation not found');
    }
    if (!DolibarrApi::_checkAccessToResource('workstation', $this->workstation->id)) {
        throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
    }
    foreach ($request_data as $field => $value) {
        if ($field == 'id') { continue; }
        if ($field === 'caller') {
            $this->workstation->context['caller'] = sanitizeVal($request_data['caller'], 'aZ09');
            continue;
        }
        if ($field == 'array_options' && is_array($value)) {
            foreach ($value as $index => $val) {
                $this->workstation->array_options[$index] = $this->_checkValForAPI('extrafields', $val, $this->workstation);
            }
            continue;
        }
        $this->workstation->$field = $this->_checkValForAPI($field, $value, $this->workstation);
    }
    $updateresult = $this->workstation->update(DolibarrApiAccess::$user);
    if ($updateresult > 0) {
        return $this->get($id);
    } else {
        throw new RestException(500, $this->workstation->error);
    }
}
```

**Added: `delete()`** — deletes a workstation, returns success array:
```php
public function delete($id)
{
    if (!DolibarrApiAccess::$user->rights->workstation->workstation->delete) {
        throw new RestException(403);
    }
    $result = $this->workstation->fetch($id);
    if (!$result) {
        throw new RestException(404, 'Workstation not found');
    }
    if (!DolibarrApi::_checkAccessToResource('workstation', $this->workstation->id)) {
        throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
    }
    if (!$this->workstation->delete(DolibarrApiAccess::$user)) {
        throw new RestException(500, 'Error when deleting workstation');
    }
    return array(
        'success' => array(
            'code' => 200,
            'message' => 'Workstation deleted'
        )
    );
}
```

**Applied via**: Copied file out, added methods via Python, copied back.
```bash
docker cp dolibarr-app:/var/www/html/workstation/class/api_workstations.class.php /tmp/
# Python: added post(), put(), delete() methods between index() and _cleanObjectDatas()
docker cp /tmp/api_workstations.class.php dolibarr-app:/var/www/html/workstation/class/api_workstations.class.php
```

## Hotfix: Interventions getLines — uncommented TODO stub + fixed method call

**File**: `/var/www/html/fichinter/class/api_interventions.class.php` (inside `dolibarr-app` container)

**Reason**: The `getLines()` handler was wrapped in `/* TODO */` and `*/` — the PHP code was written but commented out. The implementation called `$this->fichinter->getLinesArray()` which doesn't exist on the `Fichinter` model. The correct method is `$this->fichinter->fetch_lines()`.

**Before** — the entire function was wrapped in `/* TODO ... */`, and called `$this->fichinter->getLinesArray()` which doesn't exist on the `Fichinter` model:
```php
/* TODO
public function getLines($id)
{
    ...
    $this->fichinter->getLinesArray();
    ...
}
*/
```

**After** — uncommented, `@return int` → `@return array`, `getLinesArray()` → `fetch_lines()`:
```php
public function getLines($id)
{
    if (!DolibarrApiAccess::$user->hasRight('ficheinter', 'lire')) {
        throw new RestException(403);
    }
    $result = $this->fichinter->fetch($id);
    if (!$result) {
        throw new RestException(404, 'Intervention not found');
    }
    if (!DolibarrApi::_checkAccessToResource('fichinter', $this->fichinter->id)) {
        throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
    }
    $this->fichinter->fetch_lines();
    $result = array();
    foreach ($this->fichinter->lines as $line) {
        array_push($result, $this->_cleanObjectDatas($line));
    }
    return $result;
}
```

**Applied via**:
```bash
docker cp dolibarr-app:/var/www/html/fichinter/class/api_interventions.class.php /tmp/
# Python: uncommented getLines, fixed method call
docker cp /tmp/api_interventions.class.php dolibarr-app:/var/www/html/fichinter/class/api_interventions.class.php
```

## Hotfix: Supplier proposals PUT — wrong update method called

**File**: `/var/www/html/supplier_proposal/class/api_supplier_proposals.class.php` (inside `dolibarr-app` container)

**Reason**: The PUT handler called `$this->supplier_proposal->update(DolibarrApiAccess::$user)` which invokes the **line-item** update method (updating `supplier_proposaldet` table, not the proposal header). The `SupplierProposal` model has no header-level `update()` method — only an `update()` for line items at line 3515. The parent class `CommonObject` provides `updateCommon(User $user)` which handles header updates correctly via the `$this->fields` array.

**Before** (line 209):
```php
if ($this->supplier_proposal->update(DolibarrApiAccess::$user) > 0) {
```

**After**:
```php
if ($this->supplier_proposal->updateCommon(DolibarrApiAccess::$user) > 0) {
```

**Applied via**:
```bash
docker cp dolibarr-app:/var/www/html/supplier_proposal/class/api_supplier_proposals.class.php /tmp/
# sed or Python: replace ->update( with ->updateCommon(
docker cp /tmp/api_supplier_proposals.class.php dolibarr-app:/var/www/html/supplier_proposal/class/api_supplier_proposals.class.php
```
