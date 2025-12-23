"""
DILVE Client - Integración con API DILVE
Endpoints: getRecordStatusX, getRecordsX, FTP extractions
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import csv
from io import StringIO

logger = logging.getLogger(__name__)

DILVE_BASE = "https://www.dilve.es/dilve/dilve"


class DilveClient:
    """Cliente para API DILVE"""

    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        self.base_url = DILVE_BASE
        self.timeout = 30

    async def get_record_status(
        self,
        from_date: str = "2025-12-22",
        record_type: str = "A"
    ) -> Dict:
        """
        getRecordStatusX - Obtiene cambios desde fecha
        
        Args:
            from_date: Formato YYYY-MM-DD
            record_type: "A" (all), "N" (new), "M" (modified), "D" (deleted)
        
        Returns:
            {
                "status": "success",
                "changes": [{"isbn": "...", "type": "N", "date": "..."}],
                "total": 123
            }
        """
        try:
            url = f"{self.base_url}/getRecordStatusX.do"
            params = {
                "user": self.user,
                "password": self.password,
                "fromDate": from_date,
                "type": record_type,
                "format": "JSON"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                # DILVE retorna CSV o JSON según formato
                data = response.json() if response.headers.get('content-type') == 'application/json' else {
                    "status": "success",
                    "message": "Use CSV format for compatibility"
                }

                logger.info(f"DILVE getRecordStatus: {data}")
                return data

        except Exception as e:
            logger.error(f"Error getting record status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "changes": []
            }

    async def get_records(
        self,
        isbns: List[str],
        metadata_format: str = "CSV"
    ) -> Dict:
        """
        getRecordsX - Obtiene registros por ISBN (máx 128)
        
        Args:
            isbns: Lista de ISBNs (máximo 128)
            metadata_format: "CSV", "XML", "JSON"
        
        Returns:
            {
                "status": "success",
                "records": [...],
                "total": 50
            }
        """
        try:
            if len(isbns) > 128:
                logger.warning(f"DILVE limit: máximo 128 ISBNs, recibidos {len(isbns)}")
                isbns = isbns[:128]

            url = f"{self.base_url}/getRecordsX.do"
            params = {
                "identifier": "|".join(isbns),
                "metadataformat": metadata_format,
                "user": self.user,
                "password": self.password
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                if metadata_format == "CSV":
                    records = self._parse_csv_response(response.text)
                else:
                    records = response.json()

                logger.info(f"DILVE getRecords: {len(records)} registros")
                return {
                    "status": "success",
                    "records": records,
                    "total": len(records)
                }

        except Exception as e:
            logger.error(f"Error getting records: {e}")
            return {
                "status": "error",
                "message": str(e),
                "records": []
            }

    @staticmethod
    def _parse_csv_response(csv_text: str) -> List[Dict]:
        """
        Parsea respuesta CSV de DILVE
        """
        try:
            reader = csv.DictReader(StringIO(csv_text))
            records = list(reader)
            return records
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            return []

    async def get_ftp_extractions(self) -> Dict:
        """
        Obtiene lista de extracciones disponibles en FTP
        ftp.dilve.es/extracciones/
        
        Returns:
            {
                "status": "success",
                "files": ["extraction_2025_12_22.csv", ...],
                "total": 5
            }
        """
        try:
            # En producción, conectar a FTP real
            # Para MVP, retorna estructura mock
            logger.info("FTP extractions - Mock mode")
            return {
                "status": "success",
                "files": [
                    "extraction_2025_12_22.csv",
                    "extraction_2025_12_21.csv",
                    "extraction_2025_12_20.csv"
                ],
                "total": 3,
                "note": "Conectar a ftp.dilve.es/extracciones/ en producción"
            }

        except Exception as e:
            logger.error(f"Error getting FTP extractions: {e}")
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }

    async def download_extraction(self, filename: str) -> Optional[str]:
        """
        Descarga archivo de extracción desde FTP
        
        Args:
            filename: Nombre del archivo (ej: extraction_2025_12_22.csv)
        
        Returns:
            Contenido CSV o None si error
        """
        try:
            # Mock: retorna CSV de ejemplo
            logger.info(f"Downloading extraction: {filename}")
            return self._get_mock_csv()

        except Exception as e:
            logger.error(f"Error downloading extraction: {e}")
            return None

    @staticmethod
    def _get_mock_csv() -> str:
        """
        Retorna CSV mock con datos sucios (para testing)
        """
        return """isbn13,titulo,autor,descripcion,precio,stock
9788496479685,TÃ­tulo con UTF-8 roto,Autor Ejemplo,"<p>DescripciÃ³n con HTML</p> &nbsp; &nbsp;",18.95,5
9788496479686,Otro TÃ­tulo,Otro Autor,"Descripción normal",22.50,0
9788496479687,TÃ­tulo Especial,Autor Especial,"<b>Negrita</b> y <i>cursiva</i>",15.00,12
9788496479688,Libro sin stock,Desconocido,"Sin descripción",0.00,0
9788496479689,Libro con acentos,José María,"Descripción con ñ y acentos",25.99,3"""


class DilveSync:
    """Gestor de sincronización DILVE"""

    def __init__(self, client: DilveClient):
        self.client = client

    async def sync_from_date(
        self,
        from_date: str,
        record_type: str = "A"
    ) -> Dict:
        """
        Sincroniza cambios desde fecha específica
        """
        try:
            # 1. Obtiene cambios
            changes = await self.client.get_record_status(from_date, record_type)

            if changes.get("status") != "success":
                return changes

            # 2. Extrae ISBNs
            isbns = [change.get("isbn") for change in changes.get("changes", [])]

            if not isbns:
                return {
                    "status": "success",
                    "message": "No changes found",
                    "records": []
                }

            # 3. Obtiene registros completos (en lotes de 128)
            all_records = []
            for i in range(0, len(isbns), 128):
                batch = isbns[i:i+128]
                result = await self.client.get_records(batch)
                all_records.extend(result.get("records", []))

            return {
                "status": "success",
                "records": all_records,
                "total": len(all_records)
            }

        except Exception as e:
            logger.error(f"Error syncing from date: {e}")
            return {
                "status": "error",
                "message": str(e),
                "records": []
            }

    async def sync_full_catalog(self) -> Dict:
        """
        Sincroniza catálogo completo (desde FTP)
        """
        try:
            # 1. Obtiene lista de extracciones
            extractions = await self.client.get_ftp_extractions()

            if extractions.get("status") != "success":
                return extractions

            # 2. Descarga última extracción
            files = extractions.get("files", [])
            if not files:
                return {
                    "status": "error",
                    "message": "No extractions available"
                }

            latest_file = files[0]
            csv_content = await self.client.download_extraction(latest_file)

            if not csv_content:
                return {
                    "status": "error",
                    "message": f"Failed to download {latest_file}"
                }

            # 3. Parsea CSV
            records = DilveClient._parse_csv_response(csv_content)

            return {
                "status": "success",
                "records": records,
                "total": len(records),
                "source": latest_file
            }

        except Exception as e:
            logger.error(f"Error syncing full catalog: {e}")
            return {
                "status": "error",
                "message": str(e),
                "records": []
            }
