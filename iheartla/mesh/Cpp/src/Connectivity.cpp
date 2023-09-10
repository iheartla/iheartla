#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "Connectivity.h"

namespace iheartmesh {

Connectivity::Connectivity(){

} 

int Connectivity::get_edge_index(int i, int j, int &sign){
    if (i < j)
    {
        sign = 1;
        return this->map_e[std::make_tuple(i, j)];
    }
    sign = -1;
    return this->map_e[std::make_tuple(j, i)];
}
int Connectivity::get_edge_index(int i, int j){
    if (i < j)
    {
        return this->map_e[std::make_tuple(i, j)];
    }
    return this->map_e[std::make_tuple(j, i)];
} 

}
