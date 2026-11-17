# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class EtlLeiloesVeicularPipeline:
    def process_item(self, item, spider):
        logger.debug(f"Processando item: {item.get('titulo_lote', item)}")
        return item
