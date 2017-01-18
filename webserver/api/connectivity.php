<?php
  include 'config.php';

  $postdata = file_get_contents("php://input");
  $requestList = json_decode($postdata, true);

  $condArr = array();
  $comIdArr = array();
  $proIdArr = array();
  $table = 'ERROR_UNKNOWN_TABLE_PLEASE_FIX';
  $mode = '';
  foreach($requestList as $req) {
    if (isset($req['value'])) {
      $mode = 'SEARCH_ONLY';
      $val = $req['value'];

      $id = '';
      if (strpos($val, 'PLA') !== false) {
        $id = 'pla_id';
        $table = 'plant_vs_compound';
      }
      elseif (strpos($val, 'COM') !== false) {
        $id = 'com_id';
        $table = 'plant_vs_compound';
      }
      elseif (strpos($val, 'PRO') !== false) {
        $id = 'pro_id';
        $table = 'protein_vs_disease';
      }
      elseif (strpos($val, 'DIS') !== false) {
        $id = 'dis_id';
        $table = 'protein_vs_disease';
      }

      $condArr[] = $id."='".$val."'";
    }
    elseif ( isset($req['comId']) and isset($req['proId']) ) {
      $mode = 'SEARCH_AND_PREDICT';
      $comId = $req['comId'];
      $proId = $req['proId'];

      $comIdArr[] = $comId;
      $proIdArr[] = $proId;

      $condArr[] = "(com_id='".$comId."'"." AND "."pro_id='".$proId."')";
      $table = 'compound_vs_protein';
    }
    elseif ( isset($req['comId']) ) {
      $mode = 'SEARCH_ONLY';
      $table = 'compound_vs_protein';
      $condArr[] = 'com_id='."'".$req['comId']."'";
    }
    elseif ( isset($req['proId']) ) {
      $mode = 'SEARCH_ONLY';
      $table = 'compound_vs_protein';
      $condArr[] = 'pro_id='."'".$req['proId']."'";
    }
  }
  $condArrLen = count($condArr);

  $respArr = array();
  for($i = 0; $i < $condArrLen; $i++) {
    // Construct the query
    $condStr = '';

    if ($mode==='SEARCH_ONLY') {// Merge the condition NOW
      for($j = 0; $j < $condArrLen; $j++) {
        $condStr = $condStr.$condArr[$j];
        if ($j<$condArrLen-1) {
          $condStr = $condStr.' OR ';
        }
      }
    }
    elseif ($mode==='SEARCH_AND_PREDICT') {
      $condStr = $condArr[$i];
    }

    $query = "SELECT * FROM ".$table." WHERE ".$condStr;

    // Execute the query
    $resp = pg_query($link, $query);
    $respLen = pg_num_rows($resp);

    if ($respLen===0 and $mode==='SEARCH_AND_PREDICT') {
      // TODO @Ajmal: run real predictors!
      $weight = '0.5';
      $source = 'predictor';
      $timestamp = '2017-01-14 00:00:00.00000';

      $row = array('com_id'=>$comIdArr[$i],'pro_id'=>$proIdArr[$i],
                   'weight'=>$weight,'source'=>$source,'timestamp'=>$timestamp);
      $respArr[] = $row;
    }
    else {
      while($row = pg_fetch_assoc($resp)){
        $respArr[] = $row;
      }
    }

    if ($mode==='SEARCH_ONLY') {// we have merged, so need one iter only
      break;
    }
  }
  header('Content-type: application/json');
  echo json_encode($respArr);
?>