from django.db import models

class CulturalEvent(models.Model):
    name = models.CharField(max_length=200, verbose_name='행사명')
    district = models.CharField(max_length=100, verbose_name='지역구')
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    description = models.TextField(verbose_name='설명', null=True, blank=True)

    class Meta:
        verbose_name = '문화축제'
        verbose_name_plural = '문화축제 목록'
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.district})"

class CulturalFacility(models.Model):
    name = models.CharField(max_length=200, verbose_name='시설명')
    facility_type = models.CharField(max_length=100, verbose_name='시설 유형')
    district = models.CharField(max_length=100, verbose_name='지역구')
    address = models.CharField(max_length=200, verbose_name='주소')
    latitude = models.FloatField(verbose_name='위도')
    longitude = models.FloatField(verbose_name='경도')

    class Meta:
        verbose_name = '문화시설'
        verbose_name_plural = '문화시설 목록'
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['facility_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.facility_type})"

class CrimeRate(models.Model):
    district = models.CharField(max_length=100, verbose_name='지역구')
    year = models.IntegerField(verbose_name='년도')
    crime_count = models.IntegerField(verbose_name='범죄 발생 건수')
    population = models.IntegerField(verbose_name='인구수')
    rate = models.FloatField(verbose_name='범죄율')

    class Meta:
        verbose_name = '범죄율'
        verbose_name_plural = '범죄율 목록'
        unique_together = ['district', 'year']
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['year']),
        ]

    def __str__(self):
        return f"{self.district} ({self.year}년)"