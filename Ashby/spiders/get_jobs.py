import scrapy
import re
import uuid
import os
import sys
from datetime import datetime, timezone
from utils.scraper_utils import find_type_of_job, get_country_location, verify_job_format
from utils.scraper_utils import generate_id
import json
import pandas
from parsel import Selector
from scrapy import signals
from scrapy.signalmanager import dispatcher

root_path = os.path.dirname(os.path.abspath(os.path.curdir))
sys.path.append(root_path)
print(root_path)

from push_mongo import push, job_exists, update
from oh_utils import *

class GetJobsSpider(scrapy.Spider):
    name = "get_jobs"
    allowed_domains = ["jobs.ashbyhq.com"]
    
    NEW_JOBS = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)
    
    def spider_closed(self, spider):
        with open("Scraping_log.log", "a+", encoding="utf-8") as log:
            log.write(f"{datetime.now(timezone.utc)} : {self.NEW_JOBS} New Jobs Scraped.\n")

    def start_requests(self):
        self.df = pandas.read_csv(os.path.relpath("./Ashby_companies_test.csv"))
        for company in self.df['companies']:
            yield scrapy.Request(url="%s"%company, callback=self.parse, meta={"zyte_api":{"browserHtml": True}, 'company_url':company})
    
    def sanitize_filename(self, url):
        return ''.join(e for e in url if e.isalnum())
    
    def parse(self, response):
        print("URL : ", response.url)

        blocks = response.xpath("//div[contains(@class,'job-posting-brief-list')]/a")
        for x in blocks:
            rel_url = x.xpath(".//@href").get()
            abs_url = "https://jobs.ashbyhq.com%s" % rel_url

            # check duplicated job
            if job_exists(abs_url):
                print("Duplicated => URL : ", abs_url)
                continue
            
            yield scrapy.Request(url=abs_url, callback=self.jobs_data)

    def jobs_data(self, response):
        schema_json_object_string = response.xpath("//script[@type='application/ld+json']/text()").get()
        schema_object = (json.loads(schema_json_object_string))
        
        main_title = (schema_object['title'])
        if(not main_title):
            main_title = response.xpath("//h1/text()").get()
        
        try:
            questions_object = str(response.xpath("//script[@nonce]/text()").get()).split('"applicationForm":')[1]
            questions_object = str(questions_object).split(',"surveyForms"')[0]
            questions_object = json.loads(questions_object)
        except:
            questions_object = {'fieldEntries': []}
            
        try:
            questions_object_ = str(response.xpath("//script[@nonce]/text()").get()).split('"surveyForms":')[1]
            questions_object_ = str(questions_object).split(',"secondaryLocationNames"')[0]
            questions_object_ = json.loads(questions_object_)
        except:
            questions_object_ = {'fieldEntries': []}
            
        final_requirements = []

        try:
            field_entries = questions_object.get('fieldEntries', [])
            field_entries.extend(questions_object_.get('fieldEntries', []))
            
            for field_entry in field_entries:
                field = field_entry.get('field', {})
                question_text = field.get('title', '')
                type_of_question = field.get('type', '').lower()
                is_required = field_entry.get('isRequired', False)
                options = field.get('selectableValues', [])
                
                final_options = []
                for option in options:
                    final_options.append(option['label'])
                
                if type_of_question == 'valueselect':
                    type_of_question = 'dropdown'
                elif type_of_question == 'file':
                    type_of_question = 'file'
                    continue
                elif type_of_question == 'boolean':
                    type_of_question = 'dropdown'
                    final_options = ['Yes', 'No']
                elif type_of_question == 'string':
                    type_of_question = 'text'
                elif type_of_question == 'number':
                    type_of_question = 'number'
                    question_text = "%s (Please answer with numbers only)" % question_text
                elif type_of_question == 'longtext':
                    type_of_question = 'text'
                else:
                    type_of_question = 'text'

                if("Name" in question_text or "Email" in question_text or "Resume" in question_text ):
                    continue

                if(not is_required):
                    continue

                final_requirements.append({
                    "name": question_text,
                    "type": type_of_question,
                    "options": final_options
                })

        except Exception as e:
            print(f"An error occurred: {e}")

        apply_now_url = "%s/application"%response.url

        quick_apply_btn = apply_now_url
        if(not quick_apply_btn):
            return

        company_logo = (schema_object['hiringOrganization']['logo'])
        if(not company_logo):
            company_logo = response.xpath("//link[contains(@href,'https://app.ashbyhq.com/api/images/org-theme-logo')]/@href").get()

        if(apply_now_url):
            
            title_enriched = main_title
            category_name = ""
            min_salary = response.xpath("//span[contains(@class,'_compensationTierSummary')]/text()").get()
            currency = ""
            if min_salary:
                for unit in ["$", "€", "£", "¥"]:
                    pos = min_salary.find("")
                    if not pos == -1:
                        currency = unit
                        break
            
            min_salary_1 = ""
            max_salary_1 = ""
            wage_type = 'yearly'

            if(min_salary):
                pass
            else:
                min_salary = ''
                
            if("hour" in min_salary):
                wage_type = "hourly"

            if("month" in min_salary):
                wage_type = "yearly"
            
            try:
                min_salary = str(min_salary).replace("\xa0",' ')
                min_salary = min_salary.split("per")[0]
                min_salary_1 = min_salary.split(" – ")[0]
                max_salary_1 = min_salary.split(" – ")[1]

                min_salary_1 = str(min_salary_1).replace("K","000").replace("$ ",'').replace(",",'').replace("per month",'').replace("per year",'').replace(" ",'')
                max_salary_1 = str(max_salary_1).replace("K","000").replace("$ ",'').replace(",",'').replace("per month",'').replace("per year",'').replace(" ",'')
                min_salary_1 = ''.join([char for char in min_salary_1 if char.isdigit()])
                max_salary_1 = ''.join([char for char in max_salary_1 if char.isdigit()])
            except:
                min_salary_1 = ''
                max_salary_1 = ''
            
            final_desc = (schema_object['description'])
            if(not final_desc):
                final_desc = response.xpath("//div[@aria-labelledby='job-overview']").get()

            company_name = (schema_object['hiringOrganization']['name'])
            if(not company_name):
                company_name = str(response.url).split("/")[3]

            try:
                company_location_locality = (schema_object['jobLocation']['address']['addressLocality'])
            except:
                company_location_locality = None
            try:
                company_location_region = (schema_object['jobLocation']['address']['addressRegion'])
            except:
                company_location_region = None
            try:
                company_location_country = (schema_object['jobLocation']['address']['addressCountry'])
            except:
                company_location_country = None

            location_components = [company_location_locality, company_location_region, company_location_country]

            filtered_location_components = [component for component in location_components if component]
            company_location = ", ".join(filtered_location_components)
            
            workplace_info = (schema_object['employmentType'])
            if(not workplace_info):
                workplace_info = response.xpath("//div[contains(@class,'workplaceTypes')]/text()").get() 

            is_remote = response.xpath("//h2[contains(text(),'Location Type')]/parent::node()/p[contains(text(),'Remote')]").get()
            if(is_remote):
                is_remote = 1
            else:
                is_remote = 0
            
            if(company_name):
                pass
            else:
                company_name = ''
            
            if(company_location):
                pass
            else:
                company_location = ''

            enriched_description = final_desc

            pattern = r'/job/(\d+)'

            match = re.search(pattern, response.url)

            job_id = str(uuid.uuid4())
            if match:
                job_id = match.group(1)
                print("Job ID:", job_id)

            if(company_location_region or company_location_country):
                city = company_location_region
                if(not city):
                    city = company_location_country
                country = get_country_location(city, is_remote)
            else:
                country = get_country_location("", is_remote)

            type_of_job = find_type_of_job(title_enriched, workplace_info, enriched_description, country)

            updated_at = datetime.now(timezone.utc)
            
            if(country):
                final_job_object = verify_job_format({
                    'job':{
                        'id': generate_id(apply_now_url),
                        'title': title_enriched,
                        'location': company_location,
                        'address': company_location,
                        'latitude': '0',  
                        'longitude': '0', 
                        'type': type_of_job,
                        'description': enriched_description,
                        'salary_type': wage_type,
                        'salary_currency': currency,
                        'min_wage': str(min_salary_1).replace("RM",'').replace(",",'').replace(" ",''),
                        'max_wage': str(max_salary_1).replace("RM",'').replace(",",'').replace(" ",''),
                        'salary_amount': "",
                        'wage_type': wage_type,
                        'category': category_name,
                        'industry': category_name,
                        'company': str(company_name).replace("Pte Ltd",'').replace("Pte.",'').replace("Ltd.",'').replace("Pte. Ltd.",'').replace("Pte. Ltd",'').replace("  ",''),
                        'company_logo': company_logo,
                        'country': country,
                        'work_hours': '',
                        'created_at': updated_at,
                        'updated_at': updated_at,
                        'tag': "",
                        'job_status': 1,
                        'expiry': '',
                        'source': response.url,
                        'apply_now_url': apply_now_url, 
                        'remote': is_remote,
                        'has_remote':1,
                        'remarks': title_enriched,
                        },
                        'requirements':final_requirements,
                        'company': {
                            'name': str(company_name).replace("Pte Ltd",'').replace("Pte.",'').replace("Ltd.",'').replace("Pte. Ltd.",'').replace("Pte. Ltd",'').replace("  ",''),
                            'logo': company_logo,
                        },
                        'raw_content': response.text,
                        "job_schema": schema_object,
                        'job_site': 'Ashby'
                    })
                
                push(final_job_object)
                self.NEW_JOBS += 1