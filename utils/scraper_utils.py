import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pycountry
import json
import os

import hashlib
def generate_id(url = ""):
    return hashlib.sha256(url.encode()).hexdigest()

# Type of job checker code
def find_type_of_job(job_title, job_workplace_info, job_description, country):
    print("---------Reached in global function---------------")
    title_matches_pt = ["part-time", "part time","part_time"]
    title_matches_in = ["internship", "intern", "Praktikum", "Pasantía", "Tirocinio", "Estágio", "Praktik", "Praksis", "Stagiu", "Staż", "Stáž", "Gyakorlat", "Стажування", "Стаж", "Praksa", "Практикант", "Harjoittelu", "Praktika", "Stazhuvannya", "Stazh", "Praktikant", "Prácticas", "Stagiaire", "Pasante", "Tirocinante", "Estagiário", "Stagiair", "Stagiar", "Stażysta", "Stážista", "Gyakornok", "Стажист", "Стажант", "Pripravnik", "Студент на пракси", "Harjoittelija", "Stážistka", "Stazhist", "Stazhant", "Becario", "Stagista"]
    title_matches_in_france = ["stage","internship", "intern", "Praktikum", "Pasantía", "Tirocinio", "Estágio", "Praktik", "Praksis", "Stagiu", "Staż", "Stáž", "Gyakorlat", "Стажування", "Стаж", "Praksa", "Практикант", "Harjoittelu", "Praktika", "Stazhuvannya", "Stazh", "Praktikant", "Prácticas", "Stagiaire", "Pasante", "Tirocinante", "Estagiário", "Stagiair", "Stagiar", "Stażysta", "Stážista", "Gyakornok", "Стажист", "Стажант", "Pripravnik", "Студент на пракси", "Harjoittelija", "Stážistka", "Stazhist", "Stazhant", "Becario", "Stagista"]
        
    desc_matches_pt = ["part-time job", "part time job", "part-time role", "part time role",
                        "part-time opportunity", "part time opportunity"]
    desc_matches_in = ["internship job", "intern job", "internship role", "intern role",
                        "internship opportunity",
                        "intern opportunity"]
    
    type_of_job = ''
    if any(re.search(r'\b%s\b' % re.escape(x), job_title, re.I) for x in title_matches_pt):
        type_of_job = "Part Time"

    elif any(re.search(r'\b%s\b' % re.escape(x), job_title, re.I) for x in title_matches_in):
        type_of_job = "Internship"

    elif any(re.search(r'\b%s\b' % re.escape(x), job_workplace_info, re.I) for x in title_matches_in):
        type_of_job = "Internship"

    elif any(re.search(r'\b%s\b' % re.escape(x), job_description, re.I) for x in desc_matches_pt):
        type_of_job = "Part Time"

    elif any(re.search(r'\b%s\b' % re.escape(x), job_description, re.I) for x in desc_matches_in):
        type_of_job = "Internship"
    
    elif(country == "FR" and any(re.search(r'\b%s\b' % re.escape(x), job_title, re.I) for x in title_matches_in_france)):            
        type_of_job = "Internship"

    else:
        type_of_job = "Full Time"

    return type_of_job

# get Country data from complete location (Also checks if WW for remote locations in specific regions)
def get_country_location(complete_location, is_remote , file_name='city_country_data.json'):

    script_dir = os.path.dirname(os.path.abspath(__file__))  

    # Construct absolute path to the JSON file
    file_path = os.path.join(script_dir, file_name)


    if(not complete_location and is_remote == 1):
        country = 'WW'
        return country
    if(not complete_location and is_remote == 0):
        return ""
    
    worldwideLocations = [
        "Africa", "AMER", "America", "Americas", "Anywhere", "Anywhere in the world",
        "ANZ", "APAC", "Arabic Gulf", "Asia", "Asia-Pacific", "Australia and New Zealand",
        "BENELUX", "BRICS", "CEE", "Central America", "Central Europe", "CIS",
        "Commonwealth", "DACH", "Eastern Europe", "EMEA", "EU", "European Union / Europe",
        "GCC", "Global", "Gulf", "Gulf Countries", "LATAM", "Latin America", "MENA",
        "Middle East", "Middle-East", "Nordic", "Nordic Countries", "NORDICS", 
        "North Africa", "SAM", "SEA", "South America", "South East Asia", 
        "Southeast Asia", "South-East Asia", "SSA", "Sub-Saharan Africa", "UE", 
        "Western Europe", "Work at home", "Work from home", "Worldwide", "WW"
    ]

    if((is_remote == 1) and ((complete_location) in worldwideLocations)):
        country = "WW"
        return country
    
    # internal functions to read and write data to file
    def read_data_from_file(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            data = {}
        return data
            
    def write_data_to_file(file_path, data):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)


    data = read_data_from_file(file_path)
                
    # Check if the city is already in the data
    if complete_location in data:
        country_code = data[complete_location]
        if(country_code == "GB"):
            country_code = "UK"
        return country_code
    
    geolocator = Nominatim(user_agent="my_geocoder_application")
    try:
        location = geolocator.geocode(complete_location)
        if location:
            address = geolocator.reverse((location.latitude, location.longitude), language='en')
            if address and 'country' in address.raw['address']:
                country_name = address.raw['address']['country']
                country = pycountry.countries.get(name=country_name)
                if country:
                    country_code = country.alpha_2
                    # Store new data in file
                    data[complete_location] = country_code
                    write_data_to_file(file_path, data)
                    if(country_code == "GB"):
                        country_code = "UK"
                    return country_code
        return None
    except GeocoderTimedOut:
        if(is_remote == 1):
            return "WW"
        else:
            return "Geocoding service time out"
    except Exception as e:
        if(is_remote == 1):
            return "WW"
        else:
            return str(e)

# Yielding function to verify if job format is correct or if any issues in the job format
def verify_job_format(job_object):
    # Example_object:
    # {
    #                 'job':{
    #                     'id':job_id,
    #                     'title': title_enriched,
    #                     'location': company_location,
    #                     'address': company_location,
    #                     'latitude': '0',  
    #                     'longitude': '0', 
    #                     'type': type_of_job,  #part-time, fulltime, internship
    #                     'description': enriched_description,  #enriched job description
    #                     'salary_type': wage_type, #monthly, yearly or skip
    #                     'salary_currency': '', #skip this
    #                     'min_wage': str(min_salary_1).replace("RM",'').replace(",",'').replace(" ",''), #minimum salary
    #                     'max_wage': str(max_salary_1).replace("RM",'').replace(",",'').replace(" ",''), #maximum salary
    #                     'salary_amount': "0",  #skip
    #                     'wage_type': wage_type, #monthly, yearly or skip
    #                     'category': category_name, #job category or "keyword" used to scrape this job #change this later based on input
    #                     'industry': category_name, #same as above, Category and industry are same
    #                     'company': str(company_name).replace("Pte Ltd",'').replace("Pte.",'').replace("Ltd.",'').replace("Pte. Ltd.",'').replace("Pte. Ltd",'').replace("  ",''), #company name
    #                     'company_logo': company_logo, #url of company logo
    #                     'country': country,  #2 letter code, use 'UK' for UK, don't use GB
    #                     'work_hours': '', #skip
    #                     'created_at': '', #skip
    #                     'expiry': '', #skip
    #                     'source': apply_now_url, #job URL, or final application URL if job is redirected
    #                     'apply_now_url': apply_now_url, 
    #                     'remote': is_remote, # 1 if job is remote, 0 if not remote
    #                     'remarks': title_enriched, #original job title before it's enriched
    #                     # 'specializations': job_specializations_final,
    #                     },
    #                     'requirements':final_requirements,
    #                     'company': {
    #                         'name': str(company_name).replace("Pte Ltd",'').replace("Pte.",'').replace("Ltd.",'').replace("Pte. Ltd.",'').replace("Pte. Ltd",'').replace("  ",''),
    #                         'logo': company_logo,
    #                     }
    #                 }
    job = {k.lower(): v for k, v in job_object.get('job', {}).items()}
    company = {k.lower(): v for k, v in job_object.get('company', {}).items()}
    requirements = job_object.get('requirements', {})
    
    # if not requirements:
    #     raise ValueError("requirements are missing")
    # if not company:
    #     raise ValueError("Company object missing")
    
    # Ensure required fields exist
    required_fields = ['id','location','address' ,'type', 'description','salary_type', 'wage_type','company','company_logo','source','apply_now_url' ,'min_wage', 'max_wage', 'country', 'remote']
    missing_fields = [field for field in required_fields if field.lower() not in job]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Validate type of job
    # valid_job_types = {"part-time", "full-time","fulltime", "Full Time" ,"internship","intern","project","project-based","side job","other","working student"}
    # if job['type'].lower() not in valid_job_types:
    #     raise ValueError(f"Invalid job type: {job['type']}")
    
    # Validate salary_type and wage_type
    valid_wage_types = {"", "hourly", "weekly", "monthly", "yearly"}
    if job['salary_type'].lower() and job['salary_type'].lower() not in valid_wage_types:
        raise ValueError(f"Invalid salary_type: {job['salary_type']}")
    if job['wage_type'].lower() and job['wage_type'].lower() not in valid_wage_types:
        raise ValueError(f"Invalid wage_type: {job['wage_type']}")
    
    # Validate min_wage and max_wage are integers or empty strings
    try:
        min_wage = int(job['min_wage']) if job['min_wage'] else 0
        max_wage = int(job['max_wage']) if job['max_wage'] else 0
        if min_wage < 0 or max_wage < 0:
            raise ValueError("Salary values must be non-negative integers")
    except ValueError:
        raise ValueError("min_wage and max_wage must be valid integers or empty strings")
    
    # Validate country is a 2-letter string
    if not re.match(r'^[A-Z]{2}$', job['country'].upper()):
        print(job['country'])
        raise ValueError(f"Invalid country code: {job['country']}")
    
    # Validate remote field is 0 or 1f
    if job['remote'] not in {0, 1}:
        raise ValueError("Remote field must be 0 or 1")
    
    return job_object  # Return original job object if all validations pass






