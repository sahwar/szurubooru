<?php
require_once 'src/core.php';
$config = configFactory();

$dbVersion = Model_Property::get('db-version');
printf('DB version = %d' . PHP_EOL, $dbVersion);

$upgrades = glob('src/Upgrades/*.sql');
natcasesort($upgrades);

foreach ($upgrades as $upgradePath)
{
	preg_match('/(\d+)\.sql/', $upgradePath, $matches);
	$upgradeVersion = intval($matches[1]);

	if ($upgradeVersion > $dbVersion)
	{
		printf('Executing %s...' . PHP_EOL, $upgradePath);
		$upgradeSql = file_get_contents($upgradePath);
		$queries = preg_split('/;\s*[\r\n]+/s', $upgradeSql);
		$queries = array_map('trim', $queries);
		foreach ($queries as $query)
		{
			echo $query . PHP_EOL;
			R::exec($query);
			echo PHP_EOL;
		}
	}

	Model_Property::set('db-version', $upgradeVersion);
}