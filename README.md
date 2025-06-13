# translator-pipeline
Using Cloud function to trigger on file upload in cloud storage and Vertext AI will identify the and detect the language and convert it into PFD
```bash
/cloud-function/
├── main.py
├── requirements.txt
└── NotoSans-Regular.ttf ✅
```
Translator-Pipeline

Usecase:-
You want to build a Cloud Function triggered by file uploads to a GCS bucket (bkt-cloud-fun/Upload/), process the file (e.g., translation or formatting), and store the result in Download/ folder within the same bucket.

1. 🗃️ Bucket Layout
```bash
bkt-cloud-fun/Upload/ – for incoming .txt or .pdf files
bkt-cloud-fun/Download/ – for translated/converted .pdf output
```

##Point to be noted here:-  why we are doing this way in cloud function if you want to keep every dependency intact than just keep every thing in a folder and follow below steps

# Link to download 
```bash
✅ Correct Download Link (Verified)
https://fonts.google.com/noto/specimen/Noto+Sans
Download NotoSans-Regular.ttf
```
Place it in your Cloud Function folder like this:
```bash
mkdir cloud-function
cd cloud-function
ls
NotoSans-Regular.ttf    main.py         requirements.txt
```
#Deploy the Cloud Function:
```bash
gcloud functions deploy translateUploadToPDF \
  --gen2 \
  --runtime=python311 \
  --entry-point=gcs_trigger \
  --trigger-bucket=bkt-cloud-fun \
  --source=. \
  --region=region \
  --memory=512MB \
  --timeout=180s \
  --set-env-vars=PROJECT_ID=project_id,REGION=region
```
  Another way 
  # Zip the directory:
  ```bash
  zip -r function.zip main.py requirements.txt NotoSans-Regular.ttf
```
# Deploy:
```bash
gcloud functions deploy translateUploadToPDF \
  --runtime python311 \
  --trigger-resource bkt-cloud-fun \
  --trigger-event google.storage.object.finalize \
  --entry-point=gcs_trigger \
  --source=function.zip \
  --memory=512MB \
  --timeout=180s \
  --set-env-vars PROJECT_ID=project_id,REGION=region
```

