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
if (!DolibarrApi::_checkAccessToResource('societe', $id)) {
    throw new RestException(403, 'Access not allowed for login '.DolibarrApiAccess::$user->login);
}

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

**Rights seeding SQL** (run on the Dolibarr database — `dolibarrdb` — after starting a fresh stack):
```sql
INSERT INTO llx_user_rights (fk_user, fk_id, entity, droit) VALUES
(1, (SELECT id FROM llx_c_actioncomm WHERE code = 'workstation' LIMIT 1), 1, 'read'),
(1, (SELECT id FROM llx_c_actioncomm WHERE code = 'workstation' LIMIT 1), 1, 'write'),
(1, (SELECT id FROM llx_c_actioncomm WHERE code = 'workstation' LIMIT 1), 1, 'delete');
```
Note: Workstation rights are stored in `llx_user_rights` with `fk_id` pointing to the module's entry in `llx_c_actioncomm`. Run this before any POST/PUT/DELETE workstation tests. The `get()`/`index()`/`getByRef()` (read) methods use the public API key permission model and do not require this seeding.

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

**Important**: Both the opening `/* TODO` and the closing `*/` must be removed. Leaving only one will orphan the other, causing a PHP parse error ("Unterminated comment") that disables every method below it in the file (including `postLine`, `putLine`, `deleteLine`, etc.).

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

## Hotfix: Tickets missing POST/DELETE contact handlers

**File**: `/var/www/html/ticket/class/api_tickets.class.php`

**Problem**: The `Tickets` API class had no `postContact()` or `deleteContact()` methods, so the routes `POST {id}/contact/{contactid}/{type}` and `DELETE {id}/contact/{contactid}/{type}` returned 404. The `Ticket` model inherits `add_contact()`, `delete_contact()`, and `liste_contact()` from `CommonObject`, so all the infrastructure for contact management existed — just no REST API endpoints. The contact type codes for tickets are `SUPPORTCLI` and `CONTRIBUTOR` (not `BILLING`). Permission subperms use English `write` (not French `creer`).

**Before** (insertion point — no contact methods exist, `delete()` is immediately followed by `_validate()`):
```php
	}



## Hotfix: Ticket delete crashes — `dol_is_dir()` undefined function

**File**: `/var/www/html/ticket/class/ticket.class.php`

**Problem**: The `Ticket::delete()` model method calls `dol_is_dir()` on line 1234, but this function is not defined in any loaded include path when the method is invoked via the REST API. This causes `PHP Fatal error: Call to undefined function dol_is_dir()`, which produces a 500 with an empty body. The native PHP `is_dir()` is functionally identical on Linux (`dol_is_dir` just calls `dol_osencode()` then `is_dir()`; `dol_osencode()` is a no-op on Linux). A second occurrence exists at line 2585 in `addFile()`.

**Before** (lines 1234, 2585):
```php
if (dol_is_dir($dir)) {
```

**After**:
```php
if (is_dir($dir)) {
```


	/**
	 * Validate fields before create or update object
	 */
	public function postContact($id, $contactid, $type, $source = 'external', $notrigger = 0)
	{
		if (!DolibarrApiAccess::$user->hasRight('ticket', 'write')) {
			throw new RestException(403);
		}

		if (empty($source)) {
			throw new RestException(400, 'Source can not be empty');
		}

		$sql_distinct_source = "SELECT DISTINCT source";
		$sql_distinct_source .= " FROM " . MAIN_DB_PREFIX . "c_type_contact";
		$sql_distinct_source .= " WHERE element LIKE 'ticket'";
		$sql_distinct_source .= " AND source IS NOT NULL";
		$sql_distinct_source .= " AND active != 0";
		$source_result = $this->db->query($sql_distinct_source);
		$source_array = [];

		if ($source_result) {
			$num = $this->db->num_rows($source_result);
			$i = 0;
			while ($i < $num) {
				$obj = $this->db->fetch_object($source_result);
				$source_kind = (string)$obj->source;
				array_push($source_array, $source_kind);
				$i++;
			}
		} else {
			throw new RestException(503, 'Error when retrieving list of ticket contact sources: ' . $this->db->lasterror());
		}
		if (!in_array($source, (array)$source_array, true)) {
			throw new RestException(400, 'Source=' . $source . ' not found in dictionary with active ticket contact types');
		}

		if (empty($type)) {
			throw new RestException(400, 'type can not be empty');
		}

		$sql_distinct_type = "SELECT DISTINCT code";
		$sql_distinct_type .= " FROM " . MAIN_DB_PREFIX . "c_type_contact";
		$sql_distinct_type .= " WHERE element LIKE 'ticket'";
		$sql_distinct_type .= " AND source='" . $this->db->escape($source) . "'";
		$sql_distinct_type .= " AND code IS NOT NULL";
		$sql_distinct_type .= " AND active != 0";
		$type_result = $this->db->query($sql_distinct_type);
		$type_array = [];

		if ($type_result) {
			$num = $this->db->num_rows($type_result);
			$i = 0;
			while ($i < $num) {
				$obj = $this->db->fetch_object($type_result);
				$type_kind = (string)$obj->code;
				array_push($type_array, $type_kind);
				$i++;
			}
		} else {
			throw new RestException(503, 'Error when retrieving list of ticket contact types: ' . $this->db->lasterror());
		}
		if (!in_array($type, (array)$type_array, true)) {
			throw new RestException(400, 'Type=' . $type . ' and Source=' . $source . ' not found in dictionary with active ticket contact types');
		}

		$result = $this->ticket->fetch($id);
		if (!$result) {
			throw new RestException(404, 'Ticket not found');
		}
		if (!DolibarrApi::_checkAccessToResource('ticket', $this->ticket->id)) {
			throw new RestException(403, 'Access not allowed for login ' . DolibarrApiAccess::$user->login);
		}

		$result = $this->ticket->add_contact($contactid, $type, $source, $notrigger);

		if ($result == 0) {
			throw new RestException(400, 'Already exists: Contact=' . $contactid . ' is already linked to the ticket=' . $id . ' as source=' . $source . ' and type=' . $type);
		} elseif ($result == -1) {
			throw new RestException(400, 'Wrong contact=' . $contactid);
		} elseif ($result == -2) {
			throw new RestException(400, 'Wrong type=' . $type);
		} elseif ($result == -3) {
			throw new RestException(400, 'Not allowed contacts');
		} elseif ($result == -4) {
			throw new RestException(400, 'ErrorCommercialNotAllowedForThirdparty');
		} elseif ($result == -5) {
			throw new RestException(400, 'Trigger failed');
		} elseif ($result == -6) {
			throw new RestException(400, 'DB_ERROR_RECORD_ALREADY_EXISTS');
		} elseif ($result == -7) {
			throw new RestException(400, 'Some other error');
		}

		if (!$result) {
			throw new RestException(500, 'Error when added the contact');
		}

		return [
			'success' => [
				'code' => 200,
				'message' => 'Contact=' . $contactid . ' linked to the ticket=' . $id . ' as ' . $source . ' ' . $type
			]
		];
	}

	/**
	 * Remove a contact from a ticket.
	 *
	 * @param int    $id           Id of ticket to update
	 * @param int    $contactid    Row key of the contact in the array contact_ids.
	 * @param string $type         Type of the contact (SUPPORTCLI, CONTRIBUTOR).
	 *
	 * @return array<string,array<string,int|string>>
	 *
	 * @url DELETE {id}/contact/{contactid}/{type}
	 *
	 * @throws RestException 401
	 * @throws RestException 404
	 * @throws RestException 500
	 */
	public function deleteContact($id, $contactid, $type)
	{
		if (!DolibarrApiAccess::$user->hasRight('ticket', 'write')) {
			throw new RestException(403);
		}

		$result = $this->ticket->fetch($id);
		if (!$result) {
			throw new RestException(404, 'Ticket not found');
		}

		if (!DolibarrApi::_checkAccessToResource('ticket', $this->ticket->id)) {
			throw new RestException(403, 'Access not allowed for login ' . DolibarrApiAccess::$user->login);
		}

		foreach (['internal', 'external'] as $source) {
			$contacts = $this->ticket->liste_contact(-1, $source);
			foreach ($contacts as $contact) {
				if ($contact['id'] == $contactid && $contact['code'] == $type) {
					$result = $this->ticket->delete_contact($contact['rowid']);

					if (!$result) {
						throw new RestException(500, 'Error when deleted the contact');
					}

					return $this->_cleanObjectDatas($this->ticket);
				}
			}
		}

		throw new RestException(404, 'Contact not found on ticket');
	}


	/**
	 * Validate fields before create or update object
```
