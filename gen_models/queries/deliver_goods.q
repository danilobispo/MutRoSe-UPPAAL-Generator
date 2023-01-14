//This file was generated from (Academic) UPPAAL 4.1.26-1 (rev. 7BCF30B7363A9518), February 2022

/*

*/
//NO_QUERY

/*
Basic formula query to verify absence of deadlocks
*/
A[] not deadlock

/*
Meant to fail, this one shows that G11 is executed if AT1 or AT2 (if AT1 fails) successfully execute, not just AT1, once again showing that the fallback structure is sound
*/
A[] var_goal_model_template.goal_G11 imply not object_get_0_failed 

/*
For all paths: Goal G11 is reached if AT1 or AT2 (in case AT1 fails)are successfully completed, it also means that G9 is completed
*/
A[] var_goal_model_template.goal_G11 imply not object_get_0_failed or object_get_0_failed and not battery_recharge_0_failed

/*
Mission complete is achieved by adopting one of the execution paths available in Equation \\ref{}
*/
A[] mission_complete imply \
(not object_get_0_failed) or (object_get_0_failed and not battery_recharge_0_failed) and \
(not objects_delivery_0_failed) or (objects_delivery_0_failed and not object_returning_0_failed) or (object_returning_0_failed and not alert_trigger_0_failed)

/*

*/
E<> mission_complete

/*

*/
E<> mission_failed
