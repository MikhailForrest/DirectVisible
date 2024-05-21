from django import forms

class TabForm(forms.Form):
    num = forms.IntegerField(label='Please Enter Number:')

class DirVis(forms.Form):
    TYPES_CHOICES =(
        ("1", "optical line of sight"), #отвечает за расчет просто по прямой
        ("2", "use frenel zones")
    )
    STEPS_OF_AZIMUTH = (
        ("1", 0.1),
        ("2", 0.25),
        ("3", 0.5),
        ("4", 1),
        ("5", 2),
        ("6", 5),
    )
    COUNTS_OF_SPLIT = (
        ("1",100),
        ("2",200),
        ("3",500),
        ("4",1000),
        ("5",2000),
    )
    position = forms.CharField(max_length=200, initial= 'Position')
    lat = forms.FloatField(label='latitude in degrees:', initial=54, min_value=-90, max_value=90)
    lon = forms.FloatField(label='longitude in degrees:',initial=41, min_value=-180, max_value=180)
    heightOnGround = forms.FloatField(label='height Of Antenna:', initial=10, min_value=-350, max_value=8000)
    heightFlight = forms.FloatField(label='height Of Aircraft:', initial=200, min_value=0, max_value=16000)
    distance_limitation_in_km = forms.FloatField(label='Distance limitation (km):', initial=5, min_value=2, max_value=450)
    typeOfCalculate = forms.ChoiceField(label='Type Of Calculation:', choices = TYPES_CHOICES)
    accuracyOfAzimuth = forms.ChoiceField(label='Step for azimuth:', choices = STEPS_OF_AZIMUTH, initial="5")
    divisionOfDistance = forms.ChoiceField(label='Division Of Distance:', choices = COUNTS_OF_SPLIT, initial="1")
    limitUpperAngle = forms.FloatField(label='limit of Upper Angle:', initial=90, min_value=0, max_value=90)
    limitLowerAngle = forms.FloatField(label='limit of Lower Angle:', initial=-1, min_value=-90, max_value=90)
    AboveGroundLevel = forms.BooleanField(label='Above Ground Level:', widget=forms.CheckboxInput(),required=False)
    isDrawingCircles = forms.BooleanField(label='Draw scale circles:', widget=forms.CheckboxInput(),required=False, initial=True)
    isDrawingRelief = forms.BooleanField(label='Draw relief:', widget=forms.CheckboxInput(),required=False)
    isUseUsersObjects = forms.BooleanField(label='Use buildings:', widget=forms.CheckboxInput(),required=False)

class forZones(forms.Form):
    heightFlight = forms.IntegerField(label='height Of Aircraft:', initial=20, min_value=0, max_value=16500)
    limitDist = forms.IntegerField(label='limit of distance:', initial=400, min_value=0, max_value=600)
    AboveGroundLevel = forms.BooleanField(label='Above Ground Level:', widget=forms.CheckboxInput(),required=False)
    DrawTracks = forms.BooleanField(label='Draw Tracks:', widget=forms.CheckboxInput(),required=False)
    PositionForFind = forms.CharField(label = 'Name of location', max_length=200, initial= 'Magas Airport')
    height_building = forms.IntegerField(label='height Of Building:', initial=20, min_value=0, max_value=1000)
    isDrawingCircles = forms.BooleanField(label='Draw scale circles:', widget=forms.CheckboxInput(),required=False, initial=True)
    
class forEnterHeight(forms.Form):
    height = forms.IntegerField(label='height Of Aircraft:', initial=20, min_value=0, max_value=1000)

class forHeigths(forms.Form):
    position = forms.CharField(label = 'Name of location', max_length=200, initial= 'Balakovo')
    AboveGroundLevel = forms.BooleanField(label='Above Ground Level:', widget=forms.CheckboxInput(),required=False)
    DrawTracks = forms.BooleanField(label='Draw Tracks:', widget=forms.CheckboxInput(),required=False)
