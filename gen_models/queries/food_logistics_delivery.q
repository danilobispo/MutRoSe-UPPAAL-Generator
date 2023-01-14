//This file was generated from (Academic) UPPAAL 4.1.26-1 (rev. 7BCF30B7363A9518), February 2022

/*

*/
//NO_QUERY

/*
Basic formula query to verify absence of deadlocks
*/
A[] not deadlock

/*
Reachability, a mission has a path of success in this given configuration
*/
E<> mission_complete

/*
Reachability, a mission has a path of failure in this given configuration
*/
E<> mission_failed

/*
Mission G6 concluded: 
For all paths, if the mission is complete it implies that the goal G6 is also complete (AT1 did not fail)
*/
A[] mission_complete imply not food_pickup_0_failed

/*
Mission G10 Concluded
For all paths, if the mission is complete it implies that the goal G6 is also complete (AT1 was completed successfully)
AND
AT2 or AT3 were completed as well
*/
A[] mission_complete imply (not food_pickup_0_failed) and (not fetch_deliver_0_failed or not table_deliver_0_failed)

/*

*/
not manipulation --> fetch_deliver_0_failed
