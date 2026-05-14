<?php

class ModelMarketingContacts extends Model
{
    public function addSendGroup($data)
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_group SET `name` = '" . $this->db->escape($data["name"]) . "', `description` = '" . $this->db->escape($data["description"]) . "'");
        $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_ = $this->db->getLastId();
        return $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_;
    }

    public function editSendGroup($group_id, $data)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("UPDATE " . DB_PREFIX . "contacts_group SET `name` = '" . $this->db->escape($data["name"]) . "', `description` = '" . $this->db->escape($data["description"]) . "' WHERE `group_id` = '" . (int) $group_id . "'");
    }

    public function getSendGroup($group_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_group WHERE `group_id` = '" . (int) $group_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getSendGroups($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "contacts_group";
        $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_ = ["name", "group_id"];
        if (isset($data["sort"]) && in_array($data["sort"], $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_)) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY " . $data["sort"];
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY name";
        }
        if (isset($data["order"]) && $data["order"] == "ASC") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
        }
        if (isset($data["start"]) || isset($data["limit"])) {
            if ($data["start"] < 0) {
                $data["start"] = 0;
            }
            if ($data["limit"] < 1) {
                $data["limit"] = 10;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getTotalSendGroups()
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(group_id) AS total FROM " . DB_PREFIX . "contacts_group");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function delSendGroup($group_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_group WHERE `group_id` = '" . (int) $group_id . "'");
    }

    public function addNewsletters($group_id, $emails, $move = false)
    {
        $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_ = 0;
        if ($this->checkLicense()) {
            foreach ($emails as $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_) {
                $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = 0;
                if (0 < $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"]) {
                    $_obfuscated_0D3F182A391A340508032D222A5C2816272410211E0611_ = $this->db->query("SELECT `newsletter` FROM " . DB_PREFIX . "customer WHERE `customer_id` = '" . (int) $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"] . "' LIMIT 1");
                    if ($_obfuscated_0D3F182A391A340508032D222A5C2816272410211E0611_->num_rows) {
                        if ($_obfuscated_0D3F182A391A340508032D222A5C2816272410211E0611_->row["newsletter"] == "1") {
                            $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_ = $this->db->query("SELECT `unsubscribe_id` FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "' LIMIT 1");
                            if ($_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->num_rows) {
                                $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->row["unsubscribe_id"];
                            }
                        } else {
                            $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_ = $this->db->query("SELECT `unsubscribe_id` FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "' LIMIT 1");
                            if ($_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->num_rows) {
                                $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->row["unsubscribe_id"];
                            } else {
                                $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_unsubscribe SET send_id = '0', customer_id = '" . (int) $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"] . "', `email` = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "', date_added = NOW()");
                                $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $this->db->getLastId();
                            }
                        }
                    }
                } else {
                    $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_ = $this->db->query("SELECT `unsubscribe_id` FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "' LIMIT 1");
                    if ($_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->num_rows) {
                        $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $_obfuscated_0D2101403936270F320C1211392B2C342F390F2B1A1622_->row["unsubscribe_id"];
                    }
                }
                if ($move) {
                    $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_newsletter WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "'");
                }
                $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_newsletter SET `group_id` = '" . (int) $group_id . "', `customer_id` = '" . (int) $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"] . "', `unsubscribe_id` = '" . (int) $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ . "', `email` = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["email"])) . "', `firstname` = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["firstname"]) . "', `lastname` = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["lastname"]) . "'");
                $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_++;
            }
        }
        return $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_;
    }

    public function movedNewsletters($group_id, $data = [])
    {
        if ($data) {
            $_obfuscated_0D3E221636391C0D0530282536260A042209362A3D0901_ = $this->getEmailsNewslettersFromGroup($group_id);
            foreach ($data as $_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_) {
                $_obfuscated_0D111F100A161F34103F19241B0F07102F2D11252B3732_ = $this->getNewsletter($_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_);
                if ($_obfuscated_0D111F100A161F34103F19241B0F07102F2D11252B3732_) {
                    if (!in_array($_obfuscated_0D111F100A161F34103F19241B0F07102F2D11252B3732_["email"], $_obfuscated_0D3E221636391C0D0530282536260A042209362A3D0901_)) {
                        $this->db->query("UPDATE " . DB_PREFIX . "contacts_newsletter SET `group_id` = '" . (int) $group_id . "' WHERE `newsletter_id` = '" . (int) $_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_ . "'");
                    } else {
                        if ($_obfuscated_0D111F100A161F34103F19241B0F07102F2D11252B3732_["group_id"] != $group_id) {
                            $this->delNewsletter($_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_);
                        }
                    }
                }
            }
        }
    }

    public function addNewsletter($data)
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_newsletter SET \n		`group_id` = '" . (int) $data["group_id"] . "', \n		`customer_id` = '" . (int) $data["customer_id"] . "', \n		`unsubscribe_id` = '" . (int) $data["unsubscribe_id"] . "', \n		`email` = '" . $this->db->escape(utf8_strtolower($data["email"])) . "'");
        $_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_ = $this->db->getLastId();
        return $_obfuscated_0D1E362A2A2F0D341E2F300B373E1D1213303C25260232_;
    }

    public function editNewsletter($newsletter_id, $data)
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_newsletter SET \n		`group_id` = '" . (int) $data["group_id"] . "', \n		`customer_id` = '" . (int) $data["customer_id"] . "', \n		`unsubscribe_id` = '" . (int) $data["unsubscribe_id"] . "', \n		`email` = '" . $this->db->escape(utf8_strtolower($data["email"])) . "' WHERE `newsletter_id` = '" . (int) $newsletter_id . "'");
    }

    public function delNewsletter($newsletter_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_newsletter WHERE `newsletter_id` = '" . (int) $newsletter_id . "'");
    }

    public function delNewsletterFromEmail($email)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_newsletter WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_email WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cron_emails WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
    }

    public function getNewsletter($newsletter_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_newsletter WHERE `newsletter_id` = '" . (int) $newsletter_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getNewslettersFromEmail($email)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_newsletter WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getNewslettersFromGroup($group_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT newsletter_id FROM " . DB_PREFIX . "contacts_newsletter WHERE `group_id` = '" . (int) $group_id . "' ORDER BY `email` ASC");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getEmailsNewslettersFromGroup($group_id)
    {
        $_obfuscated_0D270A0E3C222A26211E3824163B261D2A260C5C5B3C01_ = [];
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT `email` FROM " . DB_PREFIX . "contacts_newsletter WHERE `group_id` = '" . (int) $group_id . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_) {
                $_obfuscated_0D270A0E3C222A26211E3824163B261D2A260C5C5B3C01_[] = $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_["email"];
            }
        }
        return $_obfuscated_0D270A0E3C222A26211E3824163B261D2A260C5C5B3C01_;
    }

    public function getEmailsFromSqlManual($data = [])
    {
        $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_ = [];
        if ($this->checkLicense()) {
            if ($data && !empty($data["sql_table"]) && !empty($data["sql_col_email"])) {
                $_obfuscated_0D1234033C1C2232282B303F3E371E281B1F36075C1E11_ = DB_PREFIX . $data["sql_table"];
                $_obfuscated_0D0E251207332A0A3D352E102F1413325C2D242E042422_ = $this->db->query("SHOW TABLES FROM `" . DB_DATABASE . "` LIKE '" . $_obfuscated_0D1234033C1C2232282B303F3E371E281B1F36075C1E11_ . "'");
                if (0 < $_obfuscated_0D0E251207332A0A3D352E102F1413325C2D242E042422_->num_rows) {
                    $_obfuscated_0D25161C072312390B30401223321F3E355B3713153501_ = $this->db->query("DESCRIBE `" . $_obfuscated_0D1234033C1C2232282B303F3E371E281B1F36075C1E11_ . "`");
                    foreach ($_obfuscated_0D25161C072312390B30401223321F3E355B3713153501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
                        $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_[] = $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["Field"];
                    }
                    if (in_array($data["sql_col_email"], $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT `" . $data["sql_col_email"] . "` AS email";
                        if (in_array($data["sql_col_firstname"], $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ", `" . $data["sql_col_firstname"] . "` AS firstname";
                        }
                        if (in_array($data["sql_col_lastname"], $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ", `" . $data["sql_col_lastname"] . "` AS lastname";
                        }
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " FROM `" . $_obfuscated_0D1234033C1C2232282B303F3E371E281B1F36075C1E11_ . "`";
                        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
                        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                            $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
                        }
                        if ($_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_) {
                            if (!empty($data["filter_start"]) && 0 < (int) $data["filter_start"]) {
                                $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = (int) $data["filter_start"];
                            } else {
                                $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = 0;
                            }
                            if (!empty($data["filter_limit"]) && $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ < (int) $data["filter_limit"]) {
                                $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = (int) $data["filter_limit"] - (int) $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_;
                            } else {
                                if (!empty($data["filter_limit"]) && (int) $data["filter_limit"] <= $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_) {
                                    $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = 1;
                                } else {
                                    $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = count($_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_);
                                }
                            }
                            $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_ = array_slice($_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_, $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_, $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_);
                        }
                    }
                }
            }
        }
        return $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_;
    }

    public function getTotalNewslettersFromGroup($group_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(newsletter_id) AS total FROM " . DB_PREFIX . "contacts_newsletter WHERE `group_id` = '" . (int) $group_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getNewsletters($data = [])
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_ = [];
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT(cn.newsletter_id), cn.unsubscribe_id, cn.customer_id, cn.email AS cemail, cn.firstname AS nfirstname, cn.lastname AS nlastname, CONCAT(cn.firstname, ' ', cn.lastname) AS nname, c.newsletter, c.firstname, c.lastname, CONCAT(c.firstname, ' ', c.lastname) AS cname, cgd.name AS customer_group, cgp.name AS cgroup FROM " . DB_PREFIX . "contacts_newsletter cn";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "contacts_group cgp ON (cn.group_id = cgp.group_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer c ON (cn.customer_id = c.customer_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer_group_description cgd ON (c.customer_group_id = cgd.customer_group_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE cn.email <> ''";
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_ = [];
            if (!empty($data["filter_name"])) {
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(cn.firstname, ' ', cn.lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(c.firstname, ' ', c.lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
            }
            if (!empty($data["filter_email"])) {
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "cn.email LIKE '%" . $this->db->escape($data["filter_email"]) . "%'";
            }
            if ($_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND " . implode(" OR ", $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_);
            }
            if (!empty($data["filter_group_id"])) {
                if (is_array($data["filter_group_id"])) {
                    $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_ = [];
                    foreach ($data["filter_group_id"] as $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_) {
                        $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_[] = "cn.group_id = '" . (int) $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_ . "'";
                    }
                    if ($_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (" . implode(" OR ", $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) . ")";
                    }
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.group_id = '" . (int) $data["filter_group_id"] . "'";
                }
            }
            if (!empty($data["filter_customer_group_id"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_group_id = '" . (int) $data["filter_customer_group_id"] . "'";
            }
            if (isset($data["filter_unsubscribe"]) && !is_null($data["filter_unsubscribe"]) && $data["filter_unsubscribe"] == "0") {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.unsubscribe_id > '0'";
            }
            if (isset($data["filter_unsubscribe"]) && !is_null($data["filter_unsubscribe"]) && $data["filter_unsubscribe"] == "1") {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.unsubscribe_id = '0'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (cgd.language_id = '" . (int) $this->config->get("config_language_id") . "' OR cgd.language_id IS null)";
            $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_ = ["cname", "cemail", "customer_group", "cgroup"];
            if (isset($data["sort"]) && in_array($data["sort"], $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_)) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY " . $data["sort"];
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY cemail";
            }
            if (isset($data["order"]) && $data["order"] == "DESC") {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
            }
            if (isset($data["start"]) || isset($data["limit"])) {
                if ($data["start"] < 0) {
                    $data["start"] = 0;
                }
                if ($data["limit"] < 1) {
                    $data["limit"] = 10;
                }
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
            }
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                $_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
            }
            if ($_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_) {
                if (!empty($data["filter_start"]) && 0 < (int) $data["filter_start"]) {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = $data["filter_start"];
                } else {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = 0;
                }
                if (!empty($data["filter_limit"]) && $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ < (int) $data["filter_limit"]) {
                    $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = (int) $data["filter_limit"] - (int) $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_;
                } else {
                    if (!empty($data["filter_limit"]) && (int) $data["filter_limit"] <= $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_) {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = 1;
                    } else {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = count($_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_);
                    }
                }
                $_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_ = array_slice($_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_, $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_, $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_);
            }
            return $_obfuscated_0D1C5B3112290525193B30300404223F370C2B5C332622_;
        } else {
            return [];
        }
    }

    public function getTotalNewsletters($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT COUNT(cn.newsletter_id) AS total FROM " . DB_PREFIX . "contacts_newsletter cn";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer c ON (cn.customer_id = c.customer_id)";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE cn.email <> ''";
        $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_ = [];
        if (!empty($data["filter_name"])) {
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(cn.firstname, ' ', cn.lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(c.firstname, ' ', c.lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
        }
        if (!empty($data["filter_email"])) {
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "cn.email LIKE '%" . $this->db->escape($data["filter_email"]) . "%'";
        }
        if ($_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND " . implode(" OR ", $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_);
        }
        if (!empty($data["filter_group_id"])) {
            if (is_array($data["filter_group_id"])) {
                $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_ = [];
                foreach ($data["filter_group_id"] as $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_) {
                    $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_[] = "cn.group_id = '" . (int) $_obfuscated_0D2B08242F091C2B0C10113C13053F401C060B07402711_ . "'";
                }
                if ($_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (" . implode(" OR ", $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) . ")";
                }
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.group_id = '" . (int) $data["filter_group_id"] . "'";
            }
        }
        if (!empty($data["filter_customer_group_id"])) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_group_id = '" . (int) $data["filter_customer_group_id"] . "'";
        }
        if (isset($data["filter_unsubscribe"]) && !is_null($data["filter_unsubscribe"]) && $data["filter_unsubscribe"] == "0") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.unsubscribe_id > '0'";
        }
        if (isset($data["filter_unsubscribe"]) && !is_null($data["filter_unsubscribe"]) && $data["filter_unsubscribe"] == "1") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND cn.unsubscribe_id = '0'";
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function addNewCron($data)
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_cron SET name = '" . $this->db->escape($data["name"]) . "', checking = '" . (int) $data["checking"] . "', status = '" . (int) $data["status"] . "', date_added = NOW()");
        $_obfuscated_0D0D1E3E1F0730352D17210E2F0E1A26321E13313E0E01_ = $this->db->getLastId();
        return $_obfuscated_0D0D1E3E1F0730352D17210E2F0E1A26321E13313E0E01_;
    }

    public function addDataCron($cron_id, $data)
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "INSERT INTO " . DB_PREFIX . "contacts_cron_data SET cron_id = '" . (int) $cron_id . "', \n			send_to = '" . $this->db->escape($data["send_to"]) . "', \n			send_to_data = '" . $this->db->escape($data["send_to_data"]) . "', \n			date_start = '" . $this->db->escape($data["date_start"]) . "', \n			date_end = '" . $this->db->escape($data["date_end"]) . "', \n			send_region = '" . (int) $data["send_region"] . "', \n			send_country_id = '" . (int) $data["send_country_id"] . "', \n			send_zone_id = '" . (int) $data["send_zone_id"] . "', \n			invers_region = '" . (int) $data["invers_region"] . "', \n			invers_product = '" . (int) $data["invers_product"] . "', \n			invers_category = '" . (int) $data["invers_category"] . "', \n			invers_customer = '" . (int) $data["invers_customer"] . "', \n			invers_client = '" . (int) $data["invers_client"] . "', \n			invers_affiliate = '" . (int) $data["invers_affiliate"] . "', \n			send_products = '" . (int) $data["send_products"] . "', \n			lang_products = '" . (int) $data["lang_products"] . "', \n			language_id = '" . (int) $data["language_id"] . "', \n			reqreview = '" . (int) $data["reqreview"] . "', \n			subject = '" . $this->db->escape($data["subject"]) . "', \n			message = '" . $this->db->escape($data["message"]) . "', \n			attachments = '" . $this->db->escape($data["attachments"]) . "', \n			attachments_cat = '" . $this->db->escape($data["attachments_cat"]) . "', \n			dopurl = '" . $this->db->escape($data["dopurl"]) . "', \n			`static` = '" . $this->db->escape($data["static"]) . "', \n			email_total = '" . (int) $data["email_total"] . "', \n			unsub_url = '" . (int) $data["unsub_url"] . "', \n			limit_start = '" . (int) $data["limit_start"] . "', \n			limit_end = '" . (int) $data["limit_end"] . "', \n			control_unsub = '" . (int) $data["control_unsub"] . "'";
            if (isset($data["emnovalid_action"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ", emnovalid_action = '" . (int) $data["emnovalid_action"] . "', embad_action = '" . (int) $data["embad_action"] . "', emsuspect_action = '" . (int) $data["emsuspect_action"] . "'";
            }
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        }
    }

    public function saveEmailsToCron($cron_id, $emails)
    {
        foreach ($emails as $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_ => $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_) {
            $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_cron_emails SET \n			cron_id = '" . (int) $cron_id . "', \n			email = '" . $this->db->escape($_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_) . "', \n			customer_id = '" . (int) $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"] . "', \n			firstname = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["firstname"]) . "', \n			lastname = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["lastname"]) . "', \n			country = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["country"]) . "', \n			`zone` = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["zone"]) . "', \n			date_added = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["date_added"]) . "'");
        }
    }

    public function getCrons($data = [])
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "contacts_cron";
            $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_ = ["name", "cron_id"];
            if (isset($data["checking"]) && $data["checking"]) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE checking = '1'";
            }
            if (isset($data["sort"]) && in_array($data["sort"], $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_)) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY " . $data["sort"];
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY cron_id";
            }
            if (isset($data["order"]) && $data["order"] == "DESC") {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
            }
            if (isset($data["start"]) || isset($data["limit"])) {
                if ($data["start"] < 0) {
                    $data["start"] = 0;
                }
                if ($data["limit"] < 1) {
                    $data["limit"] = 10;
                }
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
            }
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
        } else {
            return [];
        }
    }

    public function getTotalCrons()
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(cron_id) AS total FROM " . DB_PREFIX . "contacts_cron");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getCron($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cron WHERE cron_id = '" . (int) $cron_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getDataCron($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cron_data WHERE cron_id = '" . (int) $cron_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getCheckCronResult($cron_id)
    {
        $_obfuscated_0D132F27211F380138060E5C063D123F0E3F1C1F1C0D11_ = $this->db->query("SELECT COUNT(email) AS total FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "' AND check_status = '1'");
        $_obfuscated_0D3C24115B1C39031A0D2F0740110B312130250C2B2932_ = $this->db->query("SELECT COUNT(email) AS total FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "' AND check_status = '2'");
        $_obfuscated_0D143D0B29170A2E2F140809372128021F3422012E3B32_ = $this->db->query("SELECT COUNT(email) AS total FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "' AND check_status = '3'");
        $_obfuscated_0D17231F292E2C070D100A362B01053519101427390C22_ = $this->db->query("SELECT COUNT(email) AS total FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "' AND check_status = '4'");
        $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_ = ["good" => $_obfuscated_0D132F27211F380138060E5C063D123F0E3F1C1F1C0D11_->row["total"], "novalid" => $_obfuscated_0D3C24115B1C39031A0D2F0740110B312130250C2B2932_->row["total"], "bad" => $_obfuscated_0D143D0B29170A2E2F140809372128021F3422012E3B32_->row["total"], "suspect" => $_obfuscated_0D17231F292E2C070D100A362B01053519101427390C22_->row["total"]];
        return $_obfuscated_0D0326232E0E0D301D12395C1312391E370A120A181622_;
    }

    public function getCheckCronResultEmails($cron_id, $data)
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "'";
        if (!empty($data["check_status"])) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND check_status = '" . (int) $data["check_status"] . "'";
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getRunCron()
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_status = '1'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
        } else {
            return false;
        }
    }

    public function editCron($cron_id, $data)
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT history_id FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "' ORDER BY history_id DESC LIMIT 1");
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                $_obfuscated_0D132A5B1B5B3C0505121B2A13221016241F3B063C2E01_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["history_id"];
                $this->db->query("UPDATE " . DB_PREFIX . "contacts_cron_history SET cron_status = '0' WHERE history_id = '" . (int) $_obfuscated_0D132A5B1B5B3C0505121B2A13221016241F3B063C2E01_ . "'");
            }
            if (!($data["status"])) {
                $this->db->query("UPDATE " . DB_PREFIX . "contacts_cron SET name = '" . $this->db->escape($data["name"]) . "', date_start = '" . $this->db->escape($data["date_start"]) . "', date_next = NULL, period = '" . (int) $data["period"] . "', step = '0', status = '" . (int) $data["status"] . "' WHERE cron_id = '" . (int) $cron_id . "'");
            } else {
                $this->db->query("UPDATE " . DB_PREFIX . "contacts_cron SET name = '" . $this->db->escape($data["name"]) . "', date_start = '" . $this->db->escape($data["date_start"]) . "', date_next = NULL, period = '" . (int) $data["period"] . "', status = '" . (int) $data["status"] . "' WHERE cron_id = '" . (int) $cron_id . "'");
            }
            $this->db->query("UPDATE " . DB_PREFIX . "contacts_cron_data SET subject = '" . $this->db->escape($data["subject"]) . "', message = '" . $this->db->escape($data["message"]) . "' WHERE cron_id = '" . (int) $cron_id . "'");
        }
    }

    public function delCron($cron_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cron WHERE cron_id = '" . (int) $cron_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cron_data WHERE cron_id = '" . (int) $cron_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cron_emails WHERE cron_id = '" . (int) $cron_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_product WHERE cron_id = '" . (int) $cron_id . "'");
        $_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_ = glob(DIR_LOGS . "ccron." . preg_replace("/[^0-9]/i", "", $cron_id) . ".*");
        if ($_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_) {
            foreach ($_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_ as $_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_) {
                if (file_exists($_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_)) {
                    unlink($_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_);
                }
            }
        }
    }

    public function getCronLogs($cron_id)
    {
        $_obfuscated_0D011A252807113B123C04371F3B300C380139105C0F01_ = [];
        $_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_ = glob(DIR_LOGS . "ccron." . preg_replace("/[^0-9]/i", "", $cron_id) . ".*");
        if ($_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_) {
            foreach ($_obfuscated_0D173F353E14380B3B342725340A0E0D120A0515013132_ as $_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_) {
                if (file_exists($_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_)) {
                    $_obfuscated_0D011A252807113B123C04371F3B300C380139105C0F01_[] = $_obfuscated_0D4002250B141C323C3E2B0A152F2140230A1E06242A22_;
                }
            }
        }
        return $_obfuscated_0D011A252807113B123C04371F3B300C380139105C0F01_;
    }

    public function getCronCount($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(history_id) AS total FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getCronStatus($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT cron_status FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "' ORDER BY history_id DESC LIMIT 1");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["cron_status"];
        } else {
            return false;
        }
    }

    public function getCronSendEmailTotal($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT SUM(count_emails) AS total FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getCronHistory($history_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cron_history WHERE history_id = '" . (int) $history_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getCronHistories($cron_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cron_history WHERE cron_id = '" . (int) $cron_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function addNewSend($store_id, $type_id)
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_cache_send SET `store_id` = '" . (int) $store_id . "', `send_type` = '" . (int) $type_id . "', date_added = NOW()");
        $_obfuscated_0D235B5B29111E391E080228172E042115093F0D272822_ = $this->db->getLastId();
        return $_obfuscated_0D235B5B29111E391E080228172E042115093F0D272822_;
    }

    public function setDataNewSend($send_id, $data)
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "UPDATE " . DB_PREFIX . "contacts_cache_send SET \n			send_to = '" . $this->db->escape($data["send_to"]) . "', \n			send_to_data = '" . $this->db->escape($data["send_to_data"]) . "', \n			send_region = '" . (int) $data["send_region"] . "', \n			send_country_id = '" . (int) $data["send_country_id"] . "', \n			send_zone_id = '" . (int) $data["send_zone_id"] . "', \n			invers_region = '" . (int) $data["invers_region"] . "', \n			invers_product = '" . (int) $data["invers_product"] . "', \n			invers_category = '" . (int) $data["invers_category"] . "', \n			invers_customer = '" . (int) $data["invers_customer"] . "', \n			invers_client = '" . (int) $data["invers_client"] . "', \n			invers_affiliate = '" . (int) $data["invers_affiliate"] . "', \n			send_products = '" . (int) $data["send_products"] . "', \n			lang_products = '" . (int) $data["lang_products"] . "', \n			language_id = '" . (int) $data["language_id"] . "', \n			reqreview = '" . (int) $data["reqreview"] . "', \n			subject = '" . $this->db->escape($data["subject"]) . "', \n			message = '" . $this->db->escape($data["message"]) . "', \n			attachments = '" . $this->db->escape($data["attachments"]) . "', \n			attachments_cat = '" . $this->db->escape($data["attachments_cat"]) . "', \n			dopurl = '" . $this->db->escape($data["dopurl"]) . "', \n			email_total = '" . (int) $data["email_total"] . "', \n			unsub_url = '" . (int) $data["unsub_url"] . "', \n			control_unsub = '" . (int) $data["control_unsub"] . "' \n			WHERE send_id = '" . (int) $send_id . "'";
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        }
    }

    public function setNewMessageDataSend($send_id, $newmessage)
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "UPDATE " . DB_PREFIX . "contacts_cache_send SET newmessage = '" . $this->db->escape($newmessage) . "' WHERE send_id = '" . (int) $send_id . "'";
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
    }

    public function getMissingDataSend()
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cache_send WHERE send_type = '1' AND `status` = '0'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
        } else {
            return false;
        }
    }

    public function getDataSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cache_send WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getMessageSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT `message` FROM " . DB_PREFIX . "contacts_cache_send WHERE send_id = '" . (int) $send_id . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["message"];
        } else {
            return false;
        }
    }

    public function getNewMessageSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT `newmessage` FROM " . DB_PREFIX . "contacts_cache_send WHERE send_id = '" . (int) $send_id . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["newmessage"];
        } else {
            return false;
        }
    }

    public function getErrorsSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT `errors` FROM " . DB_PREFIX . "contacts_cache_send WHERE send_id = '" . (int) $send_id . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["errors"];
        } else {
            return false;
        }
    }

    public function addErrorSend($send_id)
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_send SET `errors` = (errors + 1) WHERE send_id = '" . (int) $send_id . "'");
    }

    public function ClearErrorsSend($send_id)
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_send SET `errors` = '0' WHERE send_id = '" . (int) $send_id . "'");
    }

    public function delDataSend($send_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_send WHERE send_id = '" . (int) $send_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_product WHERE send_id = '" . (int) $send_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_email WHERE send_id = '" . (int) $send_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_views WHERE send_id = '" . (int) $send_id . "'");
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_clicks WHERE send_id = '" . (int) $send_id . "'");
    }

    public function setCompleteDataSend($send_id, $email_total = 0)
    {
        if (0 < $email_total) {
            $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_send SET `status` = '1', email_total = '" . (int) $email_total . "' WHERE send_id = '" . (int) $send_id . "'");
        } else {
            $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_send SET `status` = '1' WHERE send_id = '" . (int) $send_id . "'");
        }
    }

    public function getCompleteDataSend($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "contacts_cache_send WHERE `status` = '1'";
        $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_ = ["date_added"];
        if (isset($data["sort"]) && in_array($data["sort"], $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_)) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY " . $data["sort"];
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY date_added";
        }
        if (isset($data["order"]) && $data["order"] == "DESC") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
        }
        if (isset($data["start"]) || isset($data["limit"])) {
            if ($data["start"] < 0) {
                $data["start"] = 0;
            }
            if ($data["limit"] < 1) {
                $data["limit"] = 10;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getTotalCompleteDataSend($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT COUNT(send_id) AS total FROM " . DB_PREFIX . "contacts_cache_send WHERE `status` = '1'";
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function setProductToSend($send_id = 0, $cron_id = 0, $data)
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_cache_product SET \n		send_id = '" . (int) $send_id . "', \n		cron_id = '" . (int) $cron_id . "', \n		type = '" . $this->db->escape($data["type"]) . "', \n		title = '" . $this->db->escape($data["title"]) . "', \n		qty = '" . (int) $data["qty"] . "', \n		cat_id = '" . $this->db->escape($data["cat_id"]) . "', \n		cat_each = '" . (int) $data["cat_each"] . "', \n		prod_id = '" . $this->db->escape($data["products"]) . "'");
    }

    public function getProductSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cache_product WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getProductsToSend($send_id, $type, $language_id = false)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        if ($this->checkLicense()) {
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT prod_id FROM " . DB_PREFIX . "contacts_cache_product WHERE send_id = '" . (int) $send_id . "' AND type = '" . $this->db->escape($type) . "'");
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                $_obfuscated_0D02380D071D2D1F1A2B021C5C123D33110C1106103722_ = explode(",", $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["prod_id"]);
                if (!empty($_obfuscated_0D02380D071D2D1F1A2B021C5C123D33110C1106103722_)) {
                    foreach ($_obfuscated_0D02380D071D2D1F1A2B021C5C123D33110C1106103722_ as $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_) {
                        $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_, $language_id);
                        if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                            $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
                        }
                    }
                }
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function delProductSend($send_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_product WHERE send_id = '" . (int) $send_id . "'");
    }

    public function saveEmailsToSend($send_id, $emails)
    {
        foreach ($emails as $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_ => $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_) {
            $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_cache_email SET \n			send_id = '" . (int) $send_id . "', \n			email = '" . $this->db->escape($_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_) . "', \n			customer_id = '" . (int) $_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["customer_id"] . "', \n			firstname = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["firstname"]) . "', \n			lastname = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["lastname"]) . "', \n			country = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["country"]) . "', \n			`zone` = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["zone"]) . "', \n			date_added = '" . $this->db->escape($_obfuscated_0D14382E360B2C30212D5C3C0304142A3C17232A121022_["date_added"]) . "'");
        }
    }

    public function getEmailsToSend($send_id, $limit)
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_cache_email WHERE send_id = '" . (int) $send_id . "' LIMIT " . $limit);
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
        } else {
            return [];
        }
    }

    public function getTotalEmailsToSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(DISTINCT email_id) AS total FROM " . DB_PREFIX . "contacts_cache_email WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function removeEmailSend($send_id, $email)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_email WHERE send_id = '" . (int) $send_id . "' AND LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
    }

    public function delEmailsSend($send_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_cache_email WHERE send_id = '" . (int) $send_id . "'");
    }

    public function addCountMails($send_id = 0, $cron_id = 0, $items = 1)
    {
        $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ = time();
        $_obfuscated_0D2C030D3037370E040D5C1B0D29061A5B143128371001_ = $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ - 86400;
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_count_mails WHERE date_send < '" . (int) $_obfuscated_0D2C030D3037370E040D5C1B0D29061A5B143128371001_ . "'");
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_count_mails SET send_id = '" . (int) $send_id . "', cron_id = '" . (int) $cron_id . "', items = '" . (int) $items . "', date_send = '" . (int) $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ . "'");
    }

    public function getCountMails()
    {
        $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_ = [];
        $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ = time();
        $_obfuscated_0D40193B1C10350916132E151711223E3E043B3F0D3E11_ = $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ - 3600;
        $_obfuscated_0D2C030D3037370E040D5C1B0D29061A5B143128371001_ = $_obfuscated_0D30351C2F1D2B0B141011110416291419133F18173C32_ - 86400;
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_count_mails WHERE date_send < '" . (int) $_obfuscated_0D2C030D3037370E040D5C1B0D29061A5B143128371001_ . "'");
        $_obfuscated_0D1C0C253B282835055C082B3C2D3510060D281C210F01_ = $this->db->query("SELECT COUNT(DISTINCT count_id) AS total FROM " . DB_PREFIX . "contacts_count_mails");
        $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_["day"] = $_obfuscated_0D1C0C253B282835055C082B3C2D3510060D281C210F01_->row["total"];
        $_obfuscated_0D2B1A0A15211C2F0E3C40192F0B0B0E071C16102D2601_ = $this->db->query("SELECT COUNT(DISTINCT count_id) AS total FROM " . DB_PREFIX . "contacts_count_mails WHERE date_send > '" . (int) $_obfuscated_0D40193B1C10350916132E151711223E3E043B3F0D3E11_ . "'");
        $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_["hour"] = $_obfuscated_0D2B1A0A15211C2F0E3C40192F0B0B0E071C16102D2601_->row["total"];
        return $_obfuscated_0D1C181D5B233E40361A0515221E0C050722065B0B0322_;
    }

    public function addUnsubscribe($email, $send_id = 0, $customer_id = 0)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT unsubscribe_id FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "' LIMIT 1");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["unsubscribe_id"];
            $this->db->query("UPDATE " . DB_PREFIX . "contacts_newsletter SET unsubscribe_id = '" . (int) $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ . "' WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        } else {
            $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_unsubscribe SET send_id = '" . (int) $send_id . "', customer_id = '" . (int) $customer_id . "', email = '" . $this->db->escape(utf8_strtolower($email)) . "', date_added = NOW()");
            $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ = $this->db->getLastId();
            $this->db->query("UPDATE " . DB_PREFIX . "contacts_newsletter SET unsubscribe_id = '" . (int) $_obfuscated_0D0E392804260808263F2239292C18042222212B3D2711_ . "' WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        }
        if (0 < $customer_id) {
            $this->db->query("UPDATE " . DB_PREFIX . "customer SET newsletter = '0' WHERE customer_id = '" . (int) $customer_id . "'");
        } else {
            $this->db->query("UPDATE " . DB_PREFIX . "customer SET newsletter = '0' WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        }
    }

    public function setSubscribe($email)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_newsletter SET unsubscribe_id = '0' WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        $this->db->query("UPDATE " . DB_PREFIX . "customer SET newsletter = '1' WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
    }

    public function checkEmailUnsubscribe($email)
    {
        $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_ = false;
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT unsubscribe_id FROM " . DB_PREFIX . "contacts_unsubscribe WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "' LIMIT 1");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_ = true;
        }
        return $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_;
    }

    public function checkCustomerNewsletter($customer_id)
    {
        $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_ = false;
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT newsletter FROM " . DB_PREFIX . "customer WHERE customer_id = '" . (int) $customer_id . "' LIMIT 1");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["newsletter"] == 1) {
                $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_ = true;
            }
        }
        return $_obfuscated_0D1C3E2E2218110E3F37373D1E262D393F3230111D2B01_;
    }

    public function getTotalUnsubscribesfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(DISTINCT email) AS total FROM " . DB_PREFIX . "contacts_unsubscribe WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getUnsubscribesfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_unsubscribe WHERE send_id = '" . (int) $send_id . "' ORDER BY date_added DESC");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getTotalViewsfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(DISTINCT email) AS total FROM " . DB_PREFIX . "contacts_views WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getViewsfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_views WHERE send_id = '" . (int) $send_id . "' ORDER BY date_added DESC");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function delViewsSend($send_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_views WHERE send_id = '" . (int) $send_id . "'");
    }

    public function getTotalClicksfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(DISTINCT email) AS total FROM " . DB_PREFIX . "contacts_clicks WHERE send_id = '" . (int) $send_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getClicksfromSend($send_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_clicks WHERE send_id = '" . (int) $send_id . "' ORDER BY date_added DESC");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function delClicksSend($send_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_clicks WHERE send_id = '" . (int) $send_id . "'");
    }

    public function getCustomerFromEmail($email)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT DISTINCT * FROM " . DB_PREFIX . "customer WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getEmailCustomers($data = [])
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_ = [];
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT c.email, c.customer_id, c.firstname, c.lastname, c.date_added, cy.name AS country, zn.name AS zone FROM " . DB_PREFIX . "customer c";
            if (!empty($data["filter_noorder"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN (SELECT DISTINCT c2.customer_id FROM " . DB_PREFIX . "customer c2 INNER JOIN `" . DB_PREFIX . "order` o ON (c2.customer_id = o.customer_id)";
            }
            $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_ = [];
            if ($this->config->get("config_complete_status")) {
                foreach ($this->config->get("config_complete_status") as $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_) {
                    $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_[] = (int) $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_;
                }
            }
            if ($_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id IN (" . implode(", ", $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) . ")";
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id > '0'";
            }
            if (!empty($data["filter_store_id"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.store_id = '" . (int) $data["filter_store_id"] . "'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ") n2 ON (c.customer_id = n2.customer_id)";
            if (!empty($data["filter_affiliate"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer_affiliate ca ON (c.customer_id = ca.customer_id)";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "address ad ON (c.customer_id = ad.customer_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "country cy ON (ad.country_id = cy.country_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN `" . DB_PREFIX . "zone` zn ON (ad.zone_id = zn.zone_id)";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE c.status = '1' AND c.email <> ''";
            if (!empty($data["filter_newsletter"]) || !empty($data["filter_unsubscribe"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.newsletter = '1'";
            }
            if (!empty($data["filter_affiliate"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ca.status = '1'";
            }
            if (!empty($data["filter_customer_group_id"]) && is_array($data["filter_customer_group_id"])) {
                $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_ = [];
                foreach ($data["filter_customer_group_id"] as $_obfuscated_0D2610230B092638113308032938323E2A1407031A1432_) {
                    $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_[] = (int) $_obfuscated_0D2610230B092638113308032938323E2A1407031A1432_;
                }
                if ($_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_group_id IN (" . implode(", ", $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) . ")";
                }
            }
            if (!empty($data["filter_customer_id"]) && is_array($data["filter_customer_id"])) {
                $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_ = [];
                foreach ($data["filter_customer_id"] as $_obfuscated_0D2610211A1E322B041821092F30153B2B1C2D340D2201_) {
                    $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_[] = (int) $_obfuscated_0D2610211A1E322B041821092F30153B2B1C2D340D2201_;
                }
                if ($_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) {
                    if (!empty($data["invers_customer"])) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_id NOT IN (" . implode(", ", $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) . ")";
                    } else {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_id IN (" . implode(", ", $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) . ")";
                    }
                }
            }
            if (!empty($data["filter_store_id"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.store_id = '" . (int) $data["filter_store_id"] . "'";
            }
            if (!empty($data["filter_date_start"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND DATE(c.date_added) >= DATE('" . $this->db->escape($data["filter_date_start"]) . "')";
            }
            if (!empty($data["filter_date_end"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND DATE(c.date_added) <= DATE('" . $this->db->escape($data["filter_date_end"]) . "')";
            }
            if (!empty($data["filter_noorder"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND n2.customer_id IS NULL";
            }
            if (!empty($data["invers_region"])) {
                if (!empty($data["filter_zone_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ad.zone_id <> '" . (int) $data["filter_zone_id"] . "'";
                } else {
                    if (!empty($data["filter_country_id"])) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ad.country_id <> '" . (int) $data["filter_country_id"] . "'";
                    }
                }
            } else {
                if (!empty($data["filter_country_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ad.country_id = '" . (int) $data["filter_country_id"] . "'";
                }
                if (!empty($data["filter_zone_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ad.zone_id = '" . (int) $data["filter_zone_id"] . "'";
                }
            }
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                $_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
            }
            if ($_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_) {
                if (!empty($data["filter_start"]) && 0 < (int) $data["filter_start"]) {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = (int) $data["filter_start"];
                } else {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = 0;
                }
                if (!empty($data["filter_limit"]) && $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ < (int) $data["filter_limit"]) {
                    $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = (int) $data["filter_limit"] - (int) $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_;
                } else {
                    if (!empty($data["filter_limit"]) && (int) $data["filter_limit"] <= $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_) {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = 1;
                    } else {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = count($_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_);
                    }
                }
                $_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_ = array_slice($_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_, $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_, $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_);
            }
            return $_obfuscated_0D0D353C310F302B1233212F28282519043F14243D0901_;
        } else {
            return [];
        }
    }

    public function getClients($data = [])
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT email, CONCAT(firstname, ' ', lastname) AS name FROM `" . DB_PREFIX . "order`";
            if ($this->config->get("contacts_client_status")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE order_status_id > '0'";
            } else {
                $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_ = [];
                if ($this->config->get("config_complete_status")) {
                    foreach ($this->config->get("config_complete_status") as $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_) {
                        $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_[] = (int) $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_;
                    }
                }
                if ($_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE order_status_id IN (" . implode(", ", $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) . ")";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE order_status_id > '0'";
                }
            }
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_ = [];
            if (!empty($data["filter_name"])) {
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(firstname, ' ', lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
            }
            if (!empty($data["filter_email"])) {
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "email LIKE '%" . $this->db->escape($data["filter_email"]) . "%'";
            }
            if (!empty($data["filter_phone"])) {
                $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "telephone LIKE '%" . $this->db->escape($data["filter_phone"]) . "%'";
            }
            if ($_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND " . implode(" OR ", $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_);
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY name ASC LIMIT 10";
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
        } else {
            return [];
        }
    }

    public function getEmailsByOrdereds($data = [])
    {
        if ($this->checkLicense()) {
            $_obfuscated_0D173F033636400932182117253503193F2133351A0C01_ = [];
            $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = false;
            if (isset($data["filter_category"])) {
                $_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_ = $this->db->query("DESCRIBE `" . DB_PREFIX . "product_to_category`");
                foreach ($_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_->rows as $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_) {
                    $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_[] = $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_["Field"];
                }
                if (in_array("main_category", $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                    $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = true;
                }
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT o.email, c.customer_id, o.firstname, o.lastname, c.date_added, o.shipping_country AS country, o.shipping_zone AS zone FROM `" . DB_PREFIX . "order` o";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer c ON (o.customer_id = c.customer_id)";
            $_obfuscated_0D15071C051608241F180916052814125C083C40341922_ = [];
            if (!empty($data["filter_products"]) && is_array($data["filter_products"])) {
                foreach ($data["filter_products"] as $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_) {
                    $_obfuscated_0D15071C051608241F180916052814125C083C40341922_[] = (int) $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_;
                }
            }
            if ($_obfuscated_0D15071C051608241F180916052814125C083C40341922_) {
                if (!empty($data["invers_product"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN (SELECT DISTINCT o2.email FROM `" . DB_PREFIX . "order` o2 INNER JOIN " . DB_PREFIX . "order_product op2 ON (o2.order_id = op2.order_id) WHERE op2.product_id IN (" . implode(", ", $_obfuscated_0D15071C051608241F180916052814125C083C40341922_) . ")) e2 ON (o.email = e2.email)";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "order_product op ON (o.order_id = op.order_id)";
                }
            }
            $_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_ = [];
            if (!empty($data["filter_category"]) && is_array($data["filter_category"])) {
                foreach ($data["filter_category"] as $_obfuscated_0D5C32331D361F3617333D0D1D38261D0A1C2337061C32_) {
                    $_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_[] = (int) $_obfuscated_0D5C32331D361F3617333D0D1D38261D0A1C2337061C32_;
                }
            }
            if ($_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_) {
                if (!empty($data["invers_category"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN (SELECT DISTINCT o2.email FROM `" . DB_PREFIX . "order` o2";
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "order_product op ON (o2.order_id = op.order_id)";
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "product_to_category p2c ON (op.product_id = p2c.product_id) WHERE p2c.category_id IN (" . implode(", ", $_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_) . ")";
                    if ($_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.main_category = '1'";
                    }
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ") e2 ON (o.email = e2.email)";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "order_product op ON (o.order_id = op.order_id)";
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "product_to_category p2c ON (op.product_id = p2c.product_id)";
                }
            }
            if ($this->config->get("contacts_client_status")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id > '0'";
            } else {
                $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_ = [];
                if ($this->config->get("config_complete_status")) {
                    foreach ($this->config->get("config_complete_status") as $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_) {
                        $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_[] = (int) $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_;
                    }
                }
                if ($_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id IN (" . implode(", ", $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) . ")";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id > '0'";
                }
            }
            if (!empty($data["filter_store_id"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.store_id = '" . (int) $data["filter_store_id"] . "'";
            }
            if (!empty($data["filter_date_start"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND DATE(o.date_added) >= DATE('" . $this->db->escape($data["filter_date_start"]) . "')";
            }
            if (!empty($data["filter_date_end"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND DATE(o.date_added) <= DATE('" . $this->db->escape($data["filter_date_end"]) . "')";
            }
            if (!empty($data["filter_client"]) && is_array($data["filter_client"])) {
                $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_ = [];
                if (!empty($data["invers_client"])) {
                    $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_[] = "o.email <> ''";
                    foreach ($data["filter_client"] as $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_) {
                        $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_[] = "LCASE(o.email) <> '" . $this->db->escape(utf8_strtolower($_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_)) . "'";
                    }
                    if ($_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (" . implode(" AND ", $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) . ")";
                    }
                } else {
                    foreach ($data["filter_client"] as $_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_) {
                        $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_[] = "LCASE(o.email) = '" . $this->db->escape(utf8_strtolower($_obfuscated_0D25021F2D3F220921242B0F1B053739320F3233290711_)) . "'";
                    }
                    if ($_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (" . implode(" OR ", $_obfuscated_0D0E02400B2B161A0A0D281F212A37260207042E262522_) . ")";
                    }
                }
            } else {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.email <> ''";
            }
            if (!empty($data["invers_region"])) {
                if (!empty($data["filter_zone_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.shipping_zone_id <> '" . (int) $data["filter_zone_id"] . "'";
                } else {
                    if (!empty($data["filter_country_id"])) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.shipping_country_id <> '" . (int) $data["filter_country_id"] . "'";
                    }
                }
            } else {
                if (!empty($data["filter_country_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.shipping_country_id = '" . (int) $data["filter_country_id"] . "'";
                }
                if (!empty($data["filter_zone_id"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.shipping_zone_id = '" . (int) $data["filter_zone_id"] . "'";
                }
            }
            if (!empty($data["filter_language_id"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.language_id = '" . (int) $data["filter_language_id"] . "'";
            }
            if (!empty($data["filter_customer_group_id"]) && is_array($data["filter_customer_group_id"])) {
                $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_ = [];
                foreach ($data["filter_customer_group_id"] as $_obfuscated_0D2610230B092638113308032938323E2A1407031A1432_) {
                    $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_[] = (int) $_obfuscated_0D2610230B092638113308032938323E2A1407031A1432_;
                }
                if ($_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND c.customer_group_id IN (" . implode(", ", $_obfuscated_0D030D35140E2D5B403D2F400F393F2C0B39072B213C32_) . ")";
                }
            }
            if ($_obfuscated_0D15071C051608241F180916052814125C083C40341922_) {
                if (!empty($data["invers_product"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND e2.email IS NULL";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND op.product_id IN (" . implode(", ", $_obfuscated_0D15071C051608241F180916052814125C083C40341922_) . ")";
                }
            }
            if ($_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_) {
                if (!empty($data["invers_category"])) {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND e2.email IS NULL";
                } else {
                    $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.category_id IN (" . implode(", ", $_obfuscated_0D0F1C0C233C0D34162A24260E1E030231300507352111_) . ")";
                    if ($_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_) {
                        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.main_category = '1'";
                    }
                }
            }
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                $_obfuscated_0D173F033636400932182117253503193F2133351A0C01_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
            }
            if ($_obfuscated_0D173F033636400932182117253503193F2133351A0C01_) {
                if (!empty($data["filter_start"]) && 0 < (int) $data["filter_start"]) {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = (int) $data["filter_start"];
                } else {
                    $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ = 0;
                }
                if (!empty($data["filter_limit"]) && $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_ < (int) $data["filter_limit"]) {
                    $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = (int) $data["filter_limit"] - (int) $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_;
                } else {
                    if (!empty($data["filter_limit"]) && (int) $data["filter_limit"] <= $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_) {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = 1;
                    } else {
                        $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_ = count($_obfuscated_0D173F033636400932182117253503193F2133351A0C01_);
                    }
                }
                $_obfuscated_0D173F033636400932182117253503193F2133351A0C01_ = array_slice($_obfuscated_0D173F033636400932182117253503193F2133351A0C01_, $_obfuscated_0D3E3E031B130E1C33285C10300E1B11252A0D22212301_, $_obfuscated_0D2140082B150E5B29402B3306190D043C0B2A0F160832_);
            }
            return $_obfuscated_0D173F033636400932182117253503193F2133351A0C01_;
        } else {
            return [];
        }
    }

    public function getCustomersGroups($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "customer_group cg LEFT JOIN " . DB_PREFIX . "customer_group_description cgd ON (cg.customer_group_id = cgd.customer_group_id) WHERE cgd.language_id = '" . (int) $this->config->get("config_language_id") . "' ORDER BY cgd.name ASC";
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getCustomersGroupDescriptions($customer_group_id)
    {
        $_obfuscated_0D3F3B26115C243B3010341A1F223F1712292E300A3B01_ = [];
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "customer_group_description WHERE customer_group_id = '" . (int) $customer_group_id . "'");
        foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
            $_obfuscated_0D3F3B26115C243B3010341A1F223F1712292E300A3B01_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["language_id"]] = ["name" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["name"], "description" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["description"]];
        }
        return $_obfuscated_0D3F3B26115C243B3010341A1F223F1712292E300A3B01_;
    }

    public function getShopCustomers($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT *, CONCAT(c.firstname, ' ', c.lastname) AS name FROM " . DB_PREFIX . "customer c";
        if (!empty($data["filter_affiliate"])) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "customer_affiliate ca ON (c.customer_id = ca.customer_id)";
        }
        $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_ = [];
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE c.status = '1'";
        if (!empty($data["filter_name"])) {
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "CONCAT(c.firstname, ' ', c.lastname) LIKE '%" . $this->db->escape($data["filter_name"]) . "%'";
        }
        if (!empty($data["filter_email"])) {
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "c.email LIKE '%" . $this->db->escape($data["filter_email"]) . "%'";
        }
        if (!empty($data["filter_affiliate"])) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND ca.status = '1'";
        }
        if ($_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= implode(" OR ", $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_);
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= ")";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY name";
        if (isset($data["order"]) && $data["order"] == "DESC") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
        }
        if (isset($data["start"]) || isset($data["limit"])) {
            if ($data["start"] < 0) {
                $data["start"] = 0;
            }
            if ($data["limit"] < 1) {
                $data["limit"] = 20;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getShopCountries($data = [])
    {
        $_obfuscated_0D312A262A1309034015153D09351222252412172A3201_ = $this->cache->get("country");
        if (!($_obfuscated_0D312A262A1309034015153D09351222252412172A3201_)) {
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "country ORDER BY name ASC");
            $_obfuscated_0D312A262A1309034015153D09351222252412172A3201_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
            $this->cache->set("country", $_obfuscated_0D312A262A1309034015153D09351222252412172A3201_);
        }
        return $_obfuscated_0D312A262A1309034015153D09351222252412172A3201_;
    }

    public function getCountry($country_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "country WHERE country_id = '" . (int) $country_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getZone($zone_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM `" . DB_PREFIX . "zone` WHERE zone_id = '" . (int) $zone_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getLanguage($language_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "language WHERE language_id = '" . (int) $language_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function getShopCurrencies($data = [])
    {
        $_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_ = $this->cache->get("currency");
        if (!($_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_)) {
            $_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_ = [];
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "currency ORDER BY title ASC");
            foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
                $_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["code"]] = ["currency_id" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["currency_id"], "title" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["title"], "code" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["code"], "symbol_left" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["symbol_left"], "symbol_right" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["symbol_right"], "decimal_place" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["decimal_place"], "value" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["value"], "status" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["status"], "date_modified" => $_obfuscated_0D2E09240A262C35131304373104050436253233361922_["date_modified"]];
            }
            $this->cache->set("currency", $_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_);
        }
        return $_obfuscated_0D0E1A210E403B09362D17073D0B352726131D10354011_;
    }

    public function getTemplates($data = [])
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT * FROM " . DB_PREFIX . "contacts_template";
        $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_ = ["name", "template_id"];
        if (isset($data["sort"]) && in_array($data["sort"], $_obfuscated_0D032424243E3107343E3921403F3637050F163C340B32_)) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY " . $data["sort"];
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY template_id";
        }
        if (isset($data["order"]) && $data["order"] == "ASC") {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ASC";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " DESC";
        }
        if (isset($data["start"]) || isset($data["limit"])) {
            if ($data["start"] < 0) {
                $data["start"] = 0;
            }
            if ($data["limit"] < 1) {
                $data["limit"] = 10;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["start"] . "," . (int) $data["limit"];
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getTotalTemplates()
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT COUNT(template_id) AS total FROM " . DB_PREFIX . "contacts_template");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["total"];
    }

    public function getTemplate($template_id)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM " . DB_PREFIX . "contacts_template WHERE template_id = '" . (int) $template_id . "'");
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row;
    }

    public function deleteTemplate($template_id)
    {
        $this->db->query("DELETE FROM " . DB_PREFIX . "contacts_template WHERE template_id = '" . (int) $template_id . "'");
    }

    public function addTemplate($data = [])
    {
        $this->db->query("INSERT INTO " . DB_PREFIX . "contacts_template SET name = '" . $this->db->escape($data["name"]) . "', subject = '" . $this->db->escape($data["subject"]) . "', message = '" . $this->db->escape($data["message"]) . "'");
        $_obfuscated_0D2C0A3D05372E39243310372903272B2A10143C2F5B11_ = $this->db->getLastId();
        return $_obfuscated_0D2C0A3D05372E39243310372903272B2A10143C2F5B11_;
    }

    public function editTemplate($template_id, $data = [])
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_template SET name = '" . $this->db->escape($data["name"]) . "', subject = '" . $this->db->escape($data["subject"]) . "', message = '" . $this->db->escape($data["message"]) . "' WHERE template_id = '" . (int) $template_id . "'");
    }

    public function markEmailReqreview($email, $products)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM `" . DB_PREFIX . "contacts_reqreview_mails` WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        if (!($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows)) {
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("INSERT `" . DB_PREFIX . "contacts_reqreview_mails` SET email = '" . $this->db->escape($email) . "'");
            $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ = $this->db->getLastId();
        } else {
            $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["revmail_id"];
        }
        if ($products) {
            $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_ = [];
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT product_id FROM `" . DB_PREFIX . "contacts_reqreview_product` WHERE revmail_id = '" . (int) $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ . "'");
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D0D222A19020A36360B3B3B03013202040A1138320E22_) {
                    $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_[] = $_obfuscated_0D0D222A19020A36360B3B3B03013202040A1138320E22_["product_id"];
                }
            }
            foreach ($products as $_obfuscated_0D36101C1B2D3730405C375C1B3C5C362A3203011D0A11_) {
                if (!in_array($_obfuscated_0D36101C1B2D3730405C375C1B3C5C362A3203011D0A11_["product_id"], $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_)) {
                    $this->db->query("INSERT `" . DB_PREFIX . "contacts_reqreview_product` SET revmail_id = '" . (int) $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ . "', product_id = '" . (int) $_obfuscated_0D36101C1B2D3730405C375C1B3C5C362A3203011D0A11_["product_id"] . "'");
                }
            }
        }
    }

    public function checkEmailReqreview($email)
    {
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM `" . DB_PREFIX . "contacts_reqreview_mails` WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["revmail_id"];
        } else {
            return false;
        }
    }

    public function checkEmailReqreviewp($email)
    {
        $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_ = [];
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM `" . DB_PREFIX . "contacts_reqreview_mails` WHERE LCASE(email) = '" . $this->db->escape(utf8_strtolower($email)) . "'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ = $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["revmail_id"];
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT product_id FROM `" . DB_PREFIX . "contacts_reqreview_product` WHERE revmail_id = '" . (int) $_obfuscated_0D370D2C07053B5B40051718323D01360118021E332F22_ . "'");
            if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
                foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D0D222A19020A36360B3B3B03013202040A1138320E22_) {
                    $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_[] = $_obfuscated_0D0D222A19020A36360B3B3B03013202040A1138320E22_["product_id"];
                }
            }
        }
        return $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_;
    }

    public function updatePurchasedp($send_id, $cron_id, $products)
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_product SET prod_id = '" . $this->db->escape(implode(",", $products)) . "' WHERE type = 'purchased' AND send_id = '" . (int) $send_id . "' AND cron_id = '" . (int) $cron_id . "'");
    }

    public function updatePurchasedc($send_id, $cron_id, $categories)
    {
        $this->db->query("UPDATE " . DB_PREFIX . "contacts_cache_product SET cat_id = '" . $this->db->escape(implode(",", $categories)) . "' WHERE type = 'purchased' AND send_id = '" . (int) $send_id . "' AND cron_id = '" . (int) $cron_id . "'");
    }

    public function getAllsCategories()
    {
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT c.category_id AS category_id, GROUP_CONCAT(cd1.name ORDER BY cp.level SEPARATOR ' &gt; ') AS name, c.parent_id, c.sort_order FROM " . DB_PREFIX . "category c \n		LEFT JOIN " . DB_PREFIX . "category_path cp ON (c.category_id = cp.category_id) \n		LEFT JOIN " . DB_PREFIX . "category_description cd1 ON (cp.path_id = cd1.category_id) \n		LEFT JOIN " . DB_PREFIX . "category_description cd2 ON (cp.category_id = cd2.category_id) \n		WHERE cd1.language_id = '" . (int) $this->config->get("config_language_id") . "' \n		AND cd2.language_id = '" . (int) $this->config->get("config_language_id") . "'";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " GROUP BY c.category_id ORDER BY name";
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        return $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows;
    }

    public function getProduct($product_id, $language_id = false, $store_id = null)
    {
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        if (!($language_id)) {
            $language_id = $this->config->get("config_language_id");
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT *, pd.name AS name, p.image, (SELECT price FROM " . DB_PREFIX . "product_special ps WHERE ps.product_id = p.product_id AND ps.customer_group_id = '" . (int) $this->config->get("config_customer_group_id") . "' AND ((ps.date_start = '0000-00-00' OR ps.date_start < '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "') AND (ps.date_end = '0000-00-00' OR ps.date_end > '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "')) ORDER BY ps.priority ASC, ps.price ASC LIMIT 1) AS special, (SELECT AVG(rating) AS total FROM " . DB_PREFIX . "review r1 WHERE r1.product_id = p.product_id AND r1.status = '1' GROUP BY r1.product_id) AS rating FROM " . DB_PREFIX . "product p \n		LEFT JOIN " . DB_PREFIX . "product_description pd ON (p.product_id = pd.product_id)";
        if (!is_null($store_id)) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id)";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE p.product_id = '" . (int) $product_id . "' AND p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'";
        if ($this->config->get("contacts_skip_price0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
        }
        if ($this->config->get("contacts_skip_qty0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND pd.language_id = '" . (int) $language_id . "'";
        if (!is_null($store_id)) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2s.store_id = '" . (int) $store_id . "'";
        }
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            return ["product_id" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["product_id"], "name" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["name"], "model" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["model"], "sku" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["sku"], "image" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["image"], "price" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["price"], "special" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["special"], "tax_class_id" => $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["tax_class_id"], "rating" => round($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->row["rating"])];
        } else {
            return false;
        }
    }

    public function getSelectedProducts($selproducts, $language_id)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        if (!empty($selproducts)) {
            foreach ($selproducts as $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_) {
                $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_, $language_id);
                if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                    $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
                }
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getProductsFromCat($category_id, $limit, $language_id, $store_id)
    {
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        if ($this->checkLicense()) {
            $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = false;
            $_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_ = $this->db->query("DESCRIBE `" . DB_PREFIX . "product_to_category`");
            foreach ($_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_->rows as $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_) {
                $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_[] = $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_["Field"];
            }
            if (in_array("main_category", $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = true;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT p2c.product_id FROM " . DB_PREFIX . "product_to_category p2c \n			LEFT JOIN " . DB_PREFIX . "product p ON (p2c.product_id = p.product_id) \n			LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id) \n			WHERE p2c.category_id = '" . (int) $category_id . "'";
            if ($_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.main_category = '1'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'";
            if ($this->config->get("contacts_skip_price0")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
            }
            if ($this->config->get("contacts_skip_qty0")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2s.store_id = '" . (int) $store_id . "'";
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY p.sort_order ASC LIMIT " . (int) $limit;
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
                $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $language_id, $store_id);
                if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                    $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
                }
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getCatSelectedProducts($category_products, $limit, $language_id, $store_id)
    {
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        if ($this->checkLicense()) {
            $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_ = [];
            $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = false;
            if (!empty($category_products)) {
                foreach ($category_products as $_obfuscated_0D5C32331D361F3617333D0D1D38261D0A1C2337061C32_) {
                    $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_[] = "p2c.category_id = '" . (int) $_obfuscated_0D5C32331D361F3617333D0D1D38261D0A1C2337061C32_ . "'";
                }
                $_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_ = $this->db->query("DESCRIBE `" . DB_PREFIX . "product_to_category`");
            }
            foreach ($_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_->rows as $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_) {
                $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_[] = $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_["Field"];
            }
            if (in_array("main_category", $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = true;
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT p2c.product_id FROM " . DB_PREFIX . "product_to_category p2c \n				LEFT JOIN " . DB_PREFIX . "product p ON (p2c.product_id = p.product_id) \n				LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id) \n				WHERE p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'";
            if ($this->config->get("contacts_skip_price0")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
            }
            if ($this->config->get("contacts_skip_qty0")) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2s.store_id = '" . (int) $store_id . "'";
            if ($_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND (" . implode(" OR ", $_obfuscated_0D1C5C391F0819023529232B23161937211D03265B5C22_) . ")";
            }
            if ($_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.main_category = '1'";
            }
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY p.sort_order ASC LIMIT " . (int) $limit;
            $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
            foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
                $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $language_id, $store_id);
                if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                    $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
                }
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getFeaturedProducts($limit, $language_id, $store_id)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        $_obfuscated_0D5B40163624323502315C352D08022D3718102C170B22_ = [];
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT * FROM `" . DB_PREFIX . "module` WHERE `code` = 'featured'");
        if ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows) {
            foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
                $_obfuscated_0D070D04360912180D361A1F3F191F165C191014112F01_ = json_decode($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["setting"], true);
                if (!empty($_obfuscated_0D070D04360912180D361A1F3F191F165C191014112F01_["product"])) {
                    foreach ($_obfuscated_0D070D04360912180D361A1F3F191F165C191014112F01_["product"] as $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_) {
                        $_obfuscated_0D5B40163624323502315C352D08022D3718102C170B22_[$_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_] = $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_;
                    }
                }
            }
        }
        if ($_obfuscated_0D5B40163624323502315C352D08022D3718102C170B22_) {
            foreach ($_obfuscated_0D5B40163624323502315C352D08022D3718102C170B22_ as $_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_) {
                $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_, $language_id, $store_id);
                if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                    $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2A241C35290928133E233E3D32361C35280B3F100632_] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
                }
            }
        }
        if ($_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_) {
            $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = array_slice($_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_, 0, (int) $limit);
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getSpecialsProducts($limit, $language_id, $store_id)
    {
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT DISTINCT ps.product_id FROM " . DB_PREFIX . "product_special ps \n		LEFT JOIN " . DB_PREFIX . "product p ON (ps.product_id = p.product_id) \n		LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id) \n		WHERE p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "' \n		AND p2s.store_id = '" . (int) $store_id . "' \n		AND ps.customer_group_id = '" . (int) $this->config->get("config_customer_group_id") . "' \n		AND ((ps.date_start = '0000-00-00' OR ps.date_start < '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "') \n		AND (ps.date_end = '0000-00-00' OR ps.date_end > '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'))";
        if ($this->config->get("contacts_skip_price0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
        }
        if ($this->config->get("contacts_skip_qty0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY p.sort_order ASC LIMIT " . (int) $limit;
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
            $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $language_id, $store_id);
            if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getBestSellerProducts($limit, $language_id, $store_id)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT op.product_id, SUM(op.quantity) AS total FROM " . DB_PREFIX . "order_product op \n		LEFT JOIN `" . DB_PREFIX . "order` o ON (op.order_id = o.order_id) \n		LEFT JOIN `" . DB_PREFIX . "product` p ON (op.product_id = p.product_id) \n		LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id)";
        $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_ = [];
        if ($this->config->get("config_complete_status")) {
            foreach ($this->config->get("config_complete_status") as $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_) {
                $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_[] = (int) $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_;
            }
        }
        if ($_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id IN (" . implode(", ", $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) . ")";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.store_id = '" . (int) $store_id . "'";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'";
        if ($this->config->get("contacts_skip_price0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
        }
        if ($this->config->get("contacts_skip_qty0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2s.store_id = '" . (int) $store_id . "'";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " GROUP BY op.product_id ORDER BY total DESC LIMIT " . (int) $limit;
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
            $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $language_id, $store_id);
            if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getLatestProducts($limit, $language_id, $store_id)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT p.product_id FROM " . DB_PREFIX . "product p \n		LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id) \n		WHERE p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "' \n		AND p2s.store_id = '" . (int) $store_id . "'";
        if ($this->config->get("contacts_skip_price0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
        }
        if ($this->config->get("contacts_skip_qty0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY p.date_added DESC LIMIT " . (int) $limit;
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
            $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $language_id, $store_id);
            if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getPurchasedsProducts($data)
    {
        $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_ = [];
        $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ = date("Y-m-d H:i") . ":00";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ = "SELECT op.product_id FROM " . DB_PREFIX . "order_product op \n		LEFT JOIN `" . DB_PREFIX . "order` o ON (op.order_id = o.order_id) \n		LEFT JOIN `" . DB_PREFIX . "product` p ON (op.product_id = p.product_id) \n		LEFT JOIN " . DB_PREFIX . "product_to_store p2s ON (p.product_id = p2s.product_id)";
        if ($data["categories"]) {
            $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = false;
            $_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_ = $this->db->query("DESCRIBE `" . DB_PREFIX . "product_to_category`");
            foreach ($_obfuscated_0D272E0E0C270F0C1316015C0D115C0D2F301A232F2232_->rows as $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_) {
                $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_[] = $_obfuscated_0D4009191E3F062A3902190712143226371F150D1D1411_["Field"];
            }
            if (in_array("main_category", $_obfuscated_0D080A31120333132310311D2124380E23091E213F1211_)) {
                $_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_ = true;
            }
            if (!($data["invers_category"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " INNER JOIN " . DB_PREFIX . "product_to_category p2c ON (op.product_id = p2c.product_id)";
            }
        }
        $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_ = [];
        if ($this->config->get("config_complete_status")) {
            foreach ($this->config->get("config_complete_status") as $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_) {
                $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_[] = (int) $_obfuscated_0D06263E0921393936390B185C5C272B181E2B07123E11_;
            }
        }
        if ($_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id IN (" . implode(", ", $_obfuscated_0D270A28111615272F3601120B2F0A270F3F192E301A11_) . ")";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " WHERE o.order_status_id > '0'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.store_id = '" . (int) $data["store_id"] . "'";
        if ($data["customer_id"]) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND o.customer_id = '" . (int) $data["customer_id"] . "'";
        } else {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND LCASE(o.email) = '" . $this->db->escape(utf8_strtolower($data["email"])) . "'";
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.status = '1' AND p.date_available <= '" . $_obfuscated_0D020A15221C2F1B123E10125B2A12111214100E090C22_ . "'";
        if ($this->config->get("contacts_skip_price0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.price > '0'";
        }
        if ($this->config->get("contacts_skip_qty0")) {
            $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.quantity > '0'";
        }
        if ($data["products"]) {
            if (!($data["invers_product"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p.product_id IN (" . implode(", ", $data["products"]) . ")";
            }
        }
        if ($data["categories"]) {
            if (!($data["invers_category"])) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.category_id IN (" . implode(", ", $data["categories"]) . ")";
            }
            if ($_obfuscated_0D103B2F1629323C1A0927022F1F161207193004350611_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2c.main_category = '1'";
            }
        }
        if ($data["reqreview"]) {
            $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_ = $this->checkEmailReqreviewp($data["email"]);
            if ($_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_) {
                $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND op.product_id NOT IN (" . implode(", ", $_obfuscated_0D301C0C270B2C123C2736100A3F0604181E2B26323222_) . ")";
            }
        }
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " AND p2s.store_id = '" . (int) $data["store_id"] . "'";
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " GROUP BY op.product_id";
        $_obfuscated_0D171C304015070F2901162328103B2727171A233C0932_ = ($this->config->get("contacts_sort_purchased_first") ? $this->config->get("contacts_sort_purchased_first") : "DESC");
        $_obfuscated_0D1B3B232D2930331C0E1E0140273D233F3C2F07242422_ = ($this->config->get("contacts_sort_purchased_last") ? $this->config->get("contacts_sort_purchased_last") : "DESC");
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " ORDER BY DATE(o.date_added) " . $_obfuscated_0D171C304015070F2901162328103B2727171A233C0932_ . ", p.price " . $_obfuscated_0D1B3B232D2930331C0E1E0140273D233F3C2F07242422_;
        $_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_ .= " LIMIT " . (int) $data["limit"];
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query($_obfuscated_0D4036301B2B1F103D24173523230110392C393B3F5B01_);
        foreach ($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->rows as $_obfuscated_0D2E09240A262C35131304373104050436253233361922_) {
            $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_ = $this->getProduct($_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"], $data["language_id"], $data["store_id"]);
            if ($_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_) {
                $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_[$_obfuscated_0D2E09240A262C35131304373104050436253233361922_["product_id"]] = $_obfuscated_0D29303D2A3B3D021D1C0A250D2E3607040C370C2D1511_;
            }
        }
        return $_obfuscated_0D3B2C033B072131353D0D220D1931392E1C06072F1601_;
    }

    public function getCronlimit($limit)
    {
        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_ = [];
        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = 16;
        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["step"] = 1;
        if ($limit) {
            $_obfuscated_0D2E09240A262C35131304373104050436253233361922_ = $limit / 60;
            if ($_obfuscated_0D2E09240A262C35131304373104050436253233361922_ < 1) {
                $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = 1;
                $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["step"] = 2;
            } else {
                if (floor($_obfuscated_0D2E09240A262C35131304373104050436253233361922_) == 1) {
                    $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = 1;
                    $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["step"] = 1;
                } else {
                    if (floor($_obfuscated_0D2E09240A262C35131304373104050436253233361922_) == 2) {
                        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = 2;
                        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["step"] = 1;
                    } else {
                        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = floor($_obfuscated_0D2E09240A262C35131304373104050436253233361922_);
                        $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["step"] = 1;
                    }
                }
            }
            if (25 < $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"]) {
                $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_["limit"] = 25;
            }
        }
        return $_obfuscated_0D3B0A36181809402B100A0340243D3327063816080201_;
    }

    public function installMailpro()
    {
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_template` (\n		`template_id` int(11) NOT NULL AUTO_INCREMENT, \n		`name` varchar(255) NOT NULL, \n		`subject` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL, \n		`message` longtext NOT NULL, \n		PRIMARY KEY (`template_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_ = $this->db->query("SELECT template_id FROM " . DB_PREFIX . "contacts_template");
        if (!($_obfuscated_0D3718191A291940170D13174007222F3E343D23163501_->num_rows)) {
            $this->db->query("INSERT INTO `" . DB_PREFIX . "contacts_template` SET `name` = 'Новое поступление товара', `message` = '&lt;p&gt;Уважаемый {name}, мы рады сообщить вам о новом поступлении продукции в наш магазин.&lt;/p&gt;&lt;p&gt;Только самая качественная и проверенная продукция! Ждем вас за покупками!&lt;/p&gt;&lt;p&gt;{latest}&lt;/p&gt;'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "contacts_template` SET `name` = 'Подарки каждому покупателю', `message` = '&lt;p&gt;&lt;span style=&quot;font-weight: bold;&quot;&gt;Здравствуйте {firstname}!&lt;/span&gt;&lt;/p&gt;&lt;p&gt;Теперь в нашем магазине {shopurl} подарки каждому покупателю!&lt;/p&gt;&lt;p&gt;Вы сами выбираете себе подарок на сумму 30% от стоимости заказа!&lt;/p&gt;&lt;p&gt;И это еще не всё, теперь доставка в {zone} у нас бесплатная!&lt;/p&gt;&lt;p&gt;Ждем вас за новыми покупками.&lt;/p&gt;&lt;p&gt;&lt;br&gt;&lt;/p&gt;&lt;p&gt;Всегда ваш,&lt;/p&gt;&lt;p&gt;{shopname}&lt;br&gt;&lt;/p&gt;'");
        }
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_unsubscribe` (\n		`unsubscribe_id` int(11) NOT NULL AUTO_INCREMENT, \n		`send_id` int(11) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`unsubscribe_id`), KEY `send_id` (`send_id`), KEY `email` (`email`(32))) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_newsletter` (\n		`newsletter_id` int(11) NOT NULL AUTO_INCREMENT, \n		`group_id` int(11) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`unsubscribe_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`firstname` varchar(64) NOT NULL, \n		`lastname` varchar(32) NOT NULL, \n		PRIMARY KEY (`newsletter_id`), KEY `group_id` (`group_id`), KEY `customer_id` (`customer_id`), KEY `email` (`email`(32))) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_views` (\n		`view_id` int(11) NOT NULL AUTO_INCREMENT, \n		`send_id` int(11) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`view_id`), KEY `send_id` (`send_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_clicks` (\n		`click_id` int(11) NOT NULL AUTO_INCREMENT, \n		`send_id` int(11) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`target` text NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`click_id`), KEY `send_id` (`send_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_group` (\n		`group_id` int(11) NOT NULL AUTO_INCREMENT, \n		`name` varchar(64) NOT NULL, \n		`description` varchar(255) NOT NULL, \n		PRIMARY KEY (`group_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cache_email` (\n		`email_id` int(11) NOT NULL AUTO_INCREMENT, \n		`send_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`firstname` varchar(64) NOT NULL, \n		`lastname` varchar(32) NOT NULL, \n		`country` varchar(32) NOT NULL, \n		`zone` varchar(32) NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`email_id`), KEY `send_id` (`send_id`), KEY `email` (`email`(32))) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cache_send` (\n		`send_id` int(11) NOT NULL AUTO_INCREMENT, \n		`store_id` int(11) NOT NULL, \n		`send_type` int(11) NOT NULL, \n		`send_to` varchar(32) NOT NULL, \n		`send_to_data` text NOT NULL, \n		`send_region` tinyint(1) NOT NULL DEFAULT '0', \n		`send_country_id` int(11) NOT NULL, \n		`send_zone_id` int(11) NOT NULL, \n		`invers_region` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_product` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_category` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_customer` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_client` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_affiliate` tinyint(1) NOT NULL DEFAULT '0', \n		`send_products` tinyint(1) NOT NULL DEFAULT '0', \n		`lang_products` int(11) NOT NULL, \n		`language_id` int(11) NOT NULL, \n		`reqreview` tinyint(1) NOT NULL DEFAULT '0', \n		`subject` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL, \n		`message` longtext NOT NULL, \n		`newmessage` longtext NOT NULL, \n		`attachments` text NOT NULL, \n		`attachments_cat` text NOT NULL, \n		`dopurl` text NOT NULL, \n		`email_total` int(11) NOT NULL, \n		`unsub_url` tinyint(1) NOT NULL DEFAULT '0', \n		`control_unsub` tinyint(1) NOT NULL DEFAULT '0', \n		`status` tinyint(1) NOT NULL DEFAULT '0', \n		`errors` int(11) NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`send_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cache_product` (\n		`product_cache_id` int(11) NOT NULL AUTO_INCREMENT, \n		`send_id` int(11) NOT NULL, \n		`cron_id` int(11) NOT NULL, \n		`type` varchar(32) NOT NULL, \n		`title` varchar(255) NOT NULL, \n		`qty` int(11) NOT NULL, \n		`cat_id` text NOT NULL, \n		`cat_each` tinyint(1) NOT NULL DEFAULT '0', \n		`prod_id` text NOT NULL, \n		PRIMARY KEY (`product_cache_id`), KEY `send_id` (`send_id`), KEY `cron_id` (`cron_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cron` (\n		`cron_id` int(11) NOT NULL AUTO_INCREMENT, \n		`name` varchar(255) NOT NULL, \n		`checking` tinyint(1) NOT NULL DEFAULT '0', \n		`date_start` datetime NULL DEFAULT NULL, \n		`date_next` datetime NULL DEFAULT NULL, \n		`period` int(11) NOT NULL, \n		`step` int(11) NOT NULL, \n		`history_id` int(11) NOT NULL, \n		`errors` int(11) NOT NULL, \n		`status` tinyint(1) NOT NULL DEFAULT '0', \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`cron_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cron_data` (\n		`cron_data_id` int(11) NOT NULL AUTO_INCREMENT, \n		`cron_id` int(11) NOT NULL, \n		`store_id` int(11) NOT NULL, \n		`send_to` varchar(32) NOT NULL, \n		`send_to_data` text NOT NULL, \n		`date_start` date NOT NULL DEFAULT '0000-00-00', \n		`date_end` date NOT NULL DEFAULT '0000-00-00', \n		`send_region` tinyint(1) NOT NULL DEFAULT '0', \n		`send_country_id` int(11) NOT NULL, \n		`send_zone_id` int(11) NOT NULL, \n		`invers_region` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_product` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_category` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_customer` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_client` tinyint(1) NOT NULL DEFAULT '0', \n		`invers_affiliate` tinyint(1) NOT NULL DEFAULT '0', \n		`send_products` tinyint(1) NOT NULL DEFAULT '0', \n		`lang_products` int(11) NOT NULL, \n		`language_id` int(11) NOT NULL, \n		`reqreview` tinyint(1) NOT NULL DEFAULT '0', \n		`subject` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL, \n		`message` longtext NOT NULL, \n		`attachments` text NOT NULL, \n		`attachments_cat` text NOT NULL, \n		`dopurl` text NOT NULL, \n		`static` varchar(32) NOT NULL, \n		`email_total` int(11) NOT NULL, \n		`unsub_url` tinyint(1) NOT NULL DEFAULT '0', \n		`control_unsub` tinyint(1) NOT NULL DEFAULT '0', \n		`limit_start` int(11) NOT NULL, \n		`limit_end` int(11) NOT NULL, \n		`emnovalid_action` tinyint(1) NOT NULL DEFAULT '0', \n		`embad_action` tinyint(1) NOT NULL DEFAULT '0', \n		`emsuspect_action` tinyint(1) NOT NULL DEFAULT '0', \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		PRIMARY KEY (`cron_data_id`), KEY `cron_id` (`cron_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cron_emails` (\n		`cemail_id` int(11) NOT NULL AUTO_INCREMENT, \n		`cron_id` int(11) NOT NULL, \n		`email` varchar(96) NOT NULL, \n		`customer_id` int(11) NOT NULL, \n		`firstname` varchar(64) NOT NULL, \n		`lastname` varchar(32) NOT NULL, \n		`country` varchar(32) NOT NULL, \n		`zone` varchar(32) NOT NULL, \n		`date_added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		`check_status` tinyint(1) NOT NULL DEFAULT '0', \n		`check_text` text NOT NULL, \n		PRIMARY KEY (`cemail_id`), KEY `cron_id` (`cron_id`), KEY `check_status` (`check_status`), KEY `email` (`email`(32))) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_cron_history` (\n		`history_id` int(11) NOT NULL AUTO_INCREMENT, \n		`cron_id` int(11) NOT NULL, \n		`send_id` int(11) NOT NULL, \n		`date_cronrun` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		`date_cronstop` datetime NOT NULL DEFAULT '0000-00-00 00:00:00', \n		`count_emails` int(11) NOT NULL, \n		`cron_status` tinyint(1) NOT NULL DEFAULT '0', \n		`text_error` varchar(255) NOT NULL, \n		`log_file` varchar(255) NOT NULL, \n		PRIMARY KEY (`history_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_count_mails` (\n		`count_id` int(11) NOT NULL AUTO_INCREMENT, \n		`cron_id` int(11) NOT NULL, \n		`send_id` int(11) NOT NULL, \n		`items` int(11) NOT NULL, \n		`date_send` int(11) NOT NULL, \n		PRIMARY KEY (`count_id`), KEY `date_send` (`date_send`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_reqreview_mails` (\n		`revmail_id` int(11) NOT NULL AUTO_INCREMENT, \n		`email` varchar(96) NOT NULL, \n		PRIMARY KEY (`revmail_id`), KEY `email` (`email`(32))) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "contacts_reqreview_product` (\n		`reqreview_product_id` int(11) NOT NULL AUTO_INCREMENT, \n		`revmail_id` int(11) NOT NULL, \n		`product_id` int(11) NOT NULL, \n		PRIMARY KEY (`reqreview_product_id`), KEY `revmail_id` (`revmail_id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8");
        $_obfuscated_0D12083E1D2F193E2D243F212B0C1E31233C1308123011_ = $this->db->query("DESCRIBE " . DB_PREFIX . "order_product");
        foreach ($_obfuscated_0D12083E1D2F193E2D243F212B0C1E31233C1308123011_->rows as $_obfuscated_0D1E3E163218252F10300E352A340B3125101A100A0232_) {
            if ($_obfuscated_0D1E3E163218252F10300E352A340B3125101A100A0232_["Field"] == "product_id") {
                $_obfuscated_0D09400C11191E03040512272C220D152C3D0B03361611_ = $_obfuscated_0D1E3E163218252F10300E352A340B3125101A100A0232_["Key"];
                if (!($_obfuscated_0D09400C11191E03040512272C220D152C3D0B03361611_)) {
                    $this->db->query("ALTER TABLE `" . DB_PREFIX . "order_product` ADD INDEX `product_id` (`product_id`)");
                }
            }
        }
        if (!($this->config->get("contacts_count_message"))) {
            $this->db->query("DELETE FROM `" . DB_PREFIX . "setting` WHERE `code` = 'contacts'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_mail_protocol', `value` = 'mail', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_mail_from', `value` = '', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_mail_parameter', `value` = '', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_smtp_host', `value` = '', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_smtp_username', `value` = '', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_smtp_password', `value` = '', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_smtp_port', `value` = '25', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_smtp_timeout', `value` = '5', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_count_message', `value` = '1', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_sleep_time', `value` = '4', `serialized` = '0'");
        }
        if (!($this->config->get("contacts_unsub_pattern"))) {
            $_obfuscated_0D3B25401D07371323122A0D5C5B5C36250B131B0E0D32_ = "/^([a-z0-9_-]+\\.)*[a-z0-9_-]+@[a-z0-9_-]+(\\.[a-z0-9_-]+)*\\.[a-z]{2,15}$/i";
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_email_pattern', `value` = '" . $this->db->escape($_obfuscated_0D3B25401D07371323122A0D5C5B5C36250B131B0E0D32_) . "', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_count_send_error', `value` = '10', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_admin_limit', `value` = '10', `serialized` = '0'");
            $_obfuscated_0D2529352A1D361317093D0A183F1A5C30071E10391501_ = rand(111111, 999999);
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_unsub_pattern', `value` = '" . (int) $_obfuscated_0D2529352A1D361317093D0A183F1A5C30071E10391501_ . "', `serialized` = '0'");
        }
        if (!($this->config->get("contacts_reply_badem"))) {
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_clear_logs', `value` = '1', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_check_mode', `value` = '1', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_global_limith', `value` = '1000', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_global_limitd', `value` = '10000', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_ignore_servers', `value` = '@mail.ru | @list.ru | @bk.ru | @inbox.ru | @hotmail.com', `serialized` = '0'");
            $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_reply_badem', `value` = 'user not found | no such user | no such mailbox | invalid mailbox | mailbox unavailable | disabled | relay access denied | relay not permitted | not exist | no such recipient | unknown recipient | recipient unknown | recipient not found | blocked | user unknown | unknown user | account is full | mailbox is full | quota exceed | over quota | overquoted | unrouteable address | name is unknown | administrative prohibition | prohibited | no mailbox here', `serialized` = '0'");
        }
        $_obfuscated_0D3E0E220C161D3B1A1E363C022F210E283B052D022301_ = fopen(DIR_LOGS . "contacts.log", "w+");
        fclose($_obfuscated_0D3E0E220C161D3B1A1E363C022F210E283B052D022301_);
        $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_install_done', `value` = '338', `serialized` = '0'");
    }

    public function checkLicense()
    {
        $_obfuscated_0D160B19222C131E35220806333603193134303F090622_ = preg_replace("/^www\\./i", "", $_SERVER["HTTP_HOST"]);
        $_obfuscated_0D055C25160B0C331A051E0C3E1E180B3D3F5C2E303D22_ = false;
        $_obfuscated_0D39112E13331110122C1A1533220E39301D3C0C290611_ = $_obfuscated_0D160B19222C131E35220806333603193134303F090622_ . "m333on3tm387";
        $_obfuscated_0D0C2C3724321B1C362D2F121115210C3B3F3502402C22_ = md5($_obfuscated_0D39112E13331110122C1A1533220E39301D3C0C290611_);
        $_obfuscated_0D1D0B25381A110D36061613020A113D232516101A3511_ = $this->config->get("contacts_license");
        if ($_obfuscated_0D1D0B25381A110D36061613020A113D232516101A3511_ == $_obfuscated_0D0C2C3724321B1C362D2F121115210C3B3F3502402C22_) {
            $_obfuscated_0D055C25160B0C331A051E0C3E1E180B3D3F5C2E303D22_ = true;
        }
        if (!($_obfuscated_0D055C25160B0C331A051E0C3E1E180B3D3F5C2E303D22_)) {
            $_obfuscated_0D055C25160B0C331A051E0C3E1E180B3D3F5C2E303D22_ = $this->getLicense();
        }
        return $_obfuscated_0D055C25160B0C331A051E0C3E1E180B3D3F5C2E303D22_;
    }

    private function getLicense()
    {
        $_obfuscated_0D1D0B25381A110D36061613020A113D232516101A3511_ = 0;
        $_obfuscated_0D160B19222C131E35220806333603193134303F090622_ = preg_replace("/^www\\./i", "", $_SERVER["HTTP_HOST"]);
        $_obfuscated_0D085C3F3F132B0E5C2B26130E022B36283328010E2A11_ = "https://opencart-group.ru/index.php?route=feed/getlic";
        $_obfuscated_0D233238060B141A023D22083E5B240C0D1C0833331E22_ = ["modul" => "mailpro", "domen" => $_obfuscated_0D160B19222C131E35220806333603193134303F090622_, "version_op" => "3.0", "version_md" => "3.3.8.7"];
        $_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_ = curl_init();
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_URL, $_obfuscated_0D085C3F3F132B0E5C2B26130E022B36283328010E2A11_);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_POST, 1);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_POSTFIELDS, $_obfuscated_0D233238060B141A023D22083E5B240C0D1C0833331E22_);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_HEADER, 0);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_SSL_VERIFYPEER, 0);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_TIMEOUT, 5);
        curl_setopt($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_, CURLOPT_CONNECTTIMEOUT, 5);
        $_obfuscated_0D140A0E2B043B0B2C5B100F225B1D18281C1F173C3032_ = curl_exec($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_);
        curl_close($_obfuscated_0D1E2E171401361A5C091F1F215C39345C1815155C2611_);
        if ($_obfuscated_0D140A0E2B043B0B2C5B100F225B1D18281C1F173C3032_) {
            $_obfuscated_0D29230A3E34343C250D3C09161237273B183D021E1401_ = explode(",", $_obfuscated_0D140A0E2B043B0B2C5B100F225B1D18281C1F173C3032_);
            if (!empty($_obfuscated_0D29230A3E34343C250D3C09161237273B183D021E1401_[1]) && $_obfuscated_0D29230A3E34343C250D3C09161237273B183D021E1401_[0] == $_obfuscated_0D160B19222C131E35220806333603193134303F090622_) {
                if (md5($_obfuscated_0D160B19222C131E35220806333603193134303F090622_ . "m333on3tm387") == $_obfuscated_0D29230A3E34343C250D3C09161237273B183D021E1401_[1]) {
                    $this->db->query("DELETE FROM `" . DB_PREFIX . "setting` WHERE `code` = 'contacts' AND `key` = 'contacts_license'");
                    $this->db->query("INSERT INTO `" . DB_PREFIX . "setting` SET `store_id` = '0', `code` = 'contacts', `key` = 'contacts_license', `value` = '" . $this->db->escape($_obfuscated_0D29230A3E34343C250D3C09161237273B183D021E1401_[1]) . "', `serialized` = '0'");
                    $_obfuscated_0D1D0B25381A110D36061613020A113D232516101A3511_ = 1;
                }
            }
        }
        return $_obfuscated_0D1D0B25381A110D36061613020A113D232516101A3511_;
    }

}
