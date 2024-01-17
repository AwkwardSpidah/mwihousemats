import os
import json
import csv
import logging as logger

logger.basicConfig(filename='app.log', filemode='w', format='[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', level=logger.DEBUG)

def load_data(filename, keep_keys):
    with open(filename, 'r') as io:
        # load file data from JSON
        file_data = json.load(io)
    
    data = {}
    for key in keep_keys:
        data[key] = file_data[key]

    return data

def path_to_name(path):
    i = path.rfind('/')

    if i == -1:
        return path

    return path[i+1:]

def build_mat_map(mats):
    mat_map = {}

    for mat_name in mats:
        mat = mats[mat_name]
        mat_details = {}
        mat_name = path_to_name(mat['hrid'])
        mat_details['requires'] = path_to_name(mat['upgradeItemHrid'])
        req_items = []
        input_items = mat.get('inputItems', [])

        if input_items != None:
            for req_item in input_items:
                new_item = {}
                new_item['name'] = path_to_name(req_item['itemHrid'])
                new_item['count'] = req_item['count']
                req_items.append(new_item)
        
        mat_details['materials'] = req_items
        mat_map[mat_name] = mat_details
    
    return mat_map

def build_houses_map(houses):
    houses_map = {}
    house_names = []

    for house_item_name in houses:
        house = houses[house_item_name]
        house_name = path_to_name(house['hrid'])
        house_names.append(house_name)
        house_upgrades = house['upgradeCostsMap']

        for house_level_name in house_upgrades:
            house_level = house_upgrades[house_level_name]
            house_level_mats = []
            for mats in house_level:
                house_level_mats.append({
                    'name': path_to_name(mats['itemHrid']),
                    'count': mats['count']
                })
            
            houses_map[f'{house_name} {house_level_name}'] = house_level_mats
    
    return house_names, houses_map

def add_mat_to_dict(mats, mat_name, mat_count):
    logger.info(f'Adding {mat_name} * {mat_count}')
    if mats.get(mat_name, None) != None:
        mats[mat_name] += mat_count
    else:
        mats[mat_name] = mat_count
    return mats

def calc_required_item_mats(needed_mats, all_mats, item, count):
    logger.info(f'calc_required_item_mats for {item}')
    item_data = all_mats.get(item, None)
    if item_data != None:
        if item_data['requires'] != '':
            calc_required_item_mats(needed_mats, all_mats, item_data['requires'], count)
        
        for item_mats in item_data['materials']:
            item_mats_lookup = all_mats.get(item_mats['name'], None)
            if item_mats_lookup != None and item_mats_lookup['requires'] != '':
                logger.info('Material ' + item_mats['name'] + ' needs ' + item_mats_lookup['requires'])
                calc_required_item_mats(needed_mats, all_mats, item_mats_lookup['requires'], item_mats['count'])

            logger.info('Adding material ' + item_mats['name'])
            calc_required_item_mats(needed_mats, all_mats, item_mats['name'], item_mats['count'])
            needed_mats = add_mat_to_dict(needed_mats, item_mats['name'], item_mats['count'] * count)
    else:
        needed_mats = add_mat_to_dict(needed_mats, item, count)

    return needed_mats

def calc_mats(house, mats, needed_mats):
    for house_mat in house:
        logger.info('Needs ' + house_mat['name'] + ' * ' + str(house_mat['count']))
        house_mat_data = mats.get(house_mat['name'], None)
        if house_mat_data != None:
            logger.info(house_mat_data)

            req_item_mats = calc_required_item_mats(needed_mats, mats, house_mat['name'], house_mat['count'])

            # if house_mat_data['requires'] != '':
            #     logger.info('Requires: ' + house_mat_data['requires'])
            #     req_item_mats = calc_required_item_mats({}, mats, house_mat_data['requires'], house_mat['count'])
            #     logger.info('Back in calc_mats')
            #     for item_mats_key in req_item_mats:
            #         needed_mats = add_mat_to_dict(needed_mats, item_mats_key, req_item_mats[item_mats_key] * house_mat['count'])
            #     needed_mats = add_mat_to_dict(needed_mats, house_mat_data['requires'], house_mat['count'])

            # for item_mats in house_mat_data['materials']:
            #     logger.info('Adding ' + item_mats['name'])
            #     needed_mats = add_mat_to_dict(needed_mats, item_mats['name'], item_mats['count'] * house_mat['count'])
            
            # needed_mats = add_mat_to_dict(needed_mats, house_mat['name'], house_mat['count'])
        else:
            needed_mats = add_mat_to_dict(needed_mats, house_mat['name'], house_mat['count'])

    return needed_mats


def calc_house_mats(houses, house_mats, all_mats):
    with open('housemats.csv', 'w') as f:
        out = csv.writer(f)
        out.writerow(['House', 'Material', 'Count'])
        for house_item in houses:
            for house_level in range(2, 8):
                house_lookup = f'{house_item} {house_level}'
                logger.info(f'Doing {house_lookup}')
                needed_mats = calc_mats(house_mats[house_lookup], all_mats, {})

                for mat_item in needed_mats:
                    out.writerow([house_lookup, mat_item, needed_mats[mat_item]])
                break
            break



def main():
    raw_mwi_data = load_data('mwidata.json', ['actionDetailMap', 'houseRoomDetailMap'])
    mwi_mat_map = build_mat_map(raw_mwi_data['actionDetailMap'])
    mwi_houses, mwi_houses_map = build_houses_map(raw_mwi_data['houseRoomDetailMap'])

    # with open('mat_data.json', 'w') as out:
    #     json.dump(mwi_mat_map, out)
    
    # with open('house_data.json', 'w') as out:
    #     json.dump(mwi_houses_map, out)

    calc_house_mats(mwi_houses, mwi_houses_map, mwi_mat_map)

if __name__ == "__main__":
    main()
