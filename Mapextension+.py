extensions = {
'blue_spawn': [(0, 0)], #Spawns blues at 0, 0
'blue_spawn_offset': 10, #Blues can spawn a maximum of 10 blocks from 0, 0
'green_spawn':[(512, 0), (512, 512, 20)] #Greens have two spawns which they can randomly spawn at. Second one will force players to spawn at height 20
#No green_spawn_offset. The script will default to 50 blocks in all directions.
'protected': [ [(0, 0, 0), (10, 10, 63)], [(10, 20, 0), (0, 10, 63)] ] #This contains two protected areas; One goes from (0, 0, 0) to (10, 10, 63), and the second one goes from (10, 20, 0) to (0, 10, 63). 
#Note that the values in the second bracket can be lower than the first bracket
'nobuild': [ [250, 250, 0], [260, 260, 63] ]
'nodestroy': [ [280, 250, 0], [220, 250, 0] ]
}