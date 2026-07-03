# BackendMods.md

## Hotfix: PHP 8.x Restler Validator crash on union types

**File**: `/var/www/html/includes/restler/framework/Luracast/Restler/Data/Validator.php`

**Problem**: PHP 8.x throws `TypeError: Illegal offset type in isset or empty` when a non-string/non-int value is used as an array key in `isset()`. The Restler framework's PHPDoc parser produces a non-scalar `$info->type` for union types like `datetime|string` (e.g., `api_tasks.class.php:654` `@param datetime|string $date`), causing `isset(static::$preFilters[$info->type])` to crash on line 427.

**Before**:
```php
isset(static::$preFilters[$info->type]) &&
```

**After**:
```php
isset(static::$preFilters[(string)$info->type]) &&
```

## Hotfix: PHP `!(-1)` bug in API user delete check

**File**: `/var/www/html/user/class/api_users.class.php`

**Problem**: `User::delete()` returns `1` on success and `-1` on error (rollback). The API handler checked `if (!$this->useraccount->delete(...))` which evaluates `!(-1)` as `false` (because `-1` is truthy in PHP), so errors were silently swallowed.

**Before**:
```php
if (!$this->useraccount->delete(DolibarrApiAccess::$user)) {
```

**After**:
```php
if ($this->useraccount->delete(DolibarrApiAccess::$user) < 0) {
```

## Hotfix: Warehouse PUT/DELETE missing `$dbtablename` in access check

**File**: `/var/www/html/product/stock/class/api_warehouses.class.php`

**Problem**: `_checkAccessToResource('stock', $this->warehouse->id)` was called without the 3rd argument `'entrepot'` (the database table name) in both the `put()` and `delete()` handlers. The GET handler correctly passes `'entrepot'`. Without the table name, `checkUserAccessToObject()` cannot find the correct DB table for the ownership SQL query and returns false for every warehouse, causing a 403 Forbidden on every PUT/DELETE regardless of permissions.

**Before** (lines 279, 349):
```php
if (!DolibarrApi::_checkAccessToResource('stock', $this->warehouse->id)) {
```

**After**:
```php
if (!DolibarrApi::_checkAccessToResource('stock', $this->warehouse->id, 'entrepot')) {
```

## Hotfix: Thirdparty representatives GET — access check before fetch + wrong fetch return check

**File**: `/var/www/html/societe/class/api_thirdparties.class.php`

**Problem**: Two bugs in `getSalesRepresentatives()`:
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

## Hotfix: Workstations missing POST/PUT/DELETE handlers

**File**: `/var/www/html/workstation/class/api_workstations.class.php`

**Problem**: Only `get()`, `getByRef()`, and `index()` methods existed — no POST/PUT/DELETE routes returned 404. The `Workstation` model class has `create()`, `update()`, and `delete()` methods, so adding the API handlers was straightforward.

**Fix**: Added `post()`, `put()`, `delete()` methods between `index()` and `_cleanObjectDatas()`. Permission checks use `$user->rights->workstation->workstation->write` (POST/PUT) and `$user->rights->workstation->workstation->delete` (DELETE). The workstation module's permission subperms use English names (`read`, `write`, `delete`) rather than French (`lire`, `creer`, `supprimer`). The admin user (aeinstein, user 1) requires these rights to be explicitly granted in `llx_user_rights`.

**Before** (insertion point):
```php
        return $obj_ret;
    }

    // phpcs:disable PEAR.NamingConventions.ValidFunctionName.PublicUnderscore
    protected function _cleanObjectDatas($object)
```

**After**:
```php
        return $obj_ret;
    }

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
            'success' => array('code' => 200, 'message' => 'Workstation deleted')
        );
    }

    // phpcs:disable PEAR.NamingConventions.ValidFunctionName.PublicUnderscore
    protected function _cleanObjectDatas($object)
```

## Hotfix: Interventions getLines — uncommented TODO stub + fixed method call

**File**: `/var/www/html/fichinter/class/api_interventions.class.php`

**Problem**: The `getLines()` handler was wrapped in `/* TODO */` — code existed but was commented out. It called `$this->fichinter->getLinesArray()` which doesn't exist on `Fichinter`. The correct method is `$this->fichinter->fetch_lines()`.

**Before**:
```php
/* TODO
public function getLines($id)
{
    if(! DolibarrApiAccess::$user->hasRight('ficheinter', 'lire')) {
        throw new RestException(403);
    }
    $result = $this->fichinter->fetch($id);
    if( ! $result ) {
        throw new RestException(404, 'Intervention not found');
    }
    if( ! DolibarrApi::_checkAccessToResource('fichinter',$this->fichinter->id)) {
        throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
    }
    $this->fichinter->getLinesArray();
    $result = array();
    foreach ($this->fichinter->lines as $line) {
        array_push($result,$this->_cleanObjectDatas($line));
    }
    return $result;
}
*/
```

**After** (removed `/* TODO` / `*/`, `@return int` → `@return array`, `getLinesArray()` → `fetch_lines()`):
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

## Hotfix: Supplier proposals PUT — wrong update method called

**File**: `/var/www/html/supplier_proposal/class/api_supplier_proposals.class.php`

**Problem**: The PUT handler called `$this->supplier_proposal->update(DolibarrApiAccess::$user)` which invokes the **line-item** update method (updating `supplier_proposaldet` table, not the proposal header). The `SupplierProposal` model has no header-level `update()` method — only an `update()` for line items at line 3515. The parent class `CommonObject` provides `updateCommon(User $user)` which handles header updates correctly via the `$this->fields` array.

**Before**:
```php
if ($this->supplier_proposal->update(DolibarrApiAccess::$user) > 0) {
```

**After**:
```php
if ($this->supplier_proposal->updateCommon(DolibarrApiAccess::$user) > 0) {
```
