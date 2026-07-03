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
