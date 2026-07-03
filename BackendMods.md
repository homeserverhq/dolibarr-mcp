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
