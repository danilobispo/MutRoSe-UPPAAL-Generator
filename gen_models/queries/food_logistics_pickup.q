//This file was generated from (Academic) UPPAAL 4.1.26-1 (rev. 7BCF30B7363A9518), February 2022

/*

*/
//NO_QUERY

/*
Basic formula query to verify absence of deadlocks
*/
A[] not deadlock

/*
For goal G7 to be satisfied (and goal G8 to be reached), either one of the task AT1 methods (pickup_with_door_opening or pickup_without_door_opening) must be satisfied
*/
A[] var_goal_model_template.goal_G8 imply (not pickup_with_door_opening_0_failed or not pickup_without_door_opening_0_failed)

/*

*/
A[] mission_complete imply (not pickup_with_door_opening_0_failed or not pickup_without_door_opening_0_failed) and not dishes_retrieval_0_failed

/*

*/
E<> mission_complete

/*

*/
E<> mission_failed
