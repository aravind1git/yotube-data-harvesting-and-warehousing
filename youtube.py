from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

#API key  connection

def Api_connect():
    Api_id="AIzaSyBvYW4sCamn0C1oAGcqfES092xeYk1gtOg"

    api_service_name="youtube"
    api_version="v3"


    youtube=build(api_service_name,api_version,developerKey=Api_id)


    return youtube

youtube=Api_connect()

#get channels information
def get_channel_info(channel_id):
    request=youtube.channels().list(
                    part="snippet,ContentDetails,statistics",
                    id=channel_id
                                        

  )

  
    response=request.execute()

    for i in response['items']:
        data=dict(channel_Name=i["snippet"]["title"],
                Channel_id=i["id"],
                Subscribers=i['statistics']['subscriberCount'],
                Views=i["statistics"]["viewCount"],
                Total_Videos=i["statistics"]["viewCount"],
                Channel_Description=i["snippet"]["description"],
                Playlist_id=i["contentDetails"]["relatedPlaylists"]["uploads"])
        return data
    
   #get video ids 

def get_video_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                                    part='contentDetails').execute()
    Playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token=None

    while True:
        response1=youtube.playlistItems().list(
                                            part='snippet',
                                            playlistId=Playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
         video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token=response1.get('nextPageToken')

        if next_page_token is None:
          break
        return video_ids


#get video info
def get_video_info(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
            part="snippet,ContentDetails,statistics",
            id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(Channel_Name=item['snippet']['channelTitle'],
                    Channel_id=item['snippet']['channelId'],
                    video_Id=item['id'],
                    Title=item['snippet']['title'],
                    Tags=item['snippet'].get('tags'),
                    Thumbnails=item['snippet']['thumbnails']['default']['url'],
                    Descripition=item['snippet'].get('description'),
                    Published_Dates=item['snippet']['publishedAt'],
                    Duration=item['contentDetails']['duration'],
                    Views=item['statistics'].get('viewCount'),
                    Likes=item['statistics'].get('likeCount'),
                    Comments=item['statistics'].get('commentCount'),
                    Favorite_Count=item['statistics']['favoriteCount'],
                    Definition=item['contentDetails']['definition'],
                    Caption_Status=item['contentDetails']['caption']
                    )
            video_data.append(data)
    return  video_data     

#get comment inform
def get_comment_info(video_ids):
 Comment_data=[]
 try:
       for video_id in video_ids:
        request=youtube.commentThreads().list(
         part="snippet",
         videoId=video_id,
         maxResults=50
    )
        response=request.execute()

       for item in response['items']:
        data=dict(Comment_Id=item['snippet']['topLevelComment']['id'],
            Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
            Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'] ,
            Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
            Comment_Published=item['snippet']['topLevelComment']['snippet']['publishedAt'])

        Comment_data.append(data)
 except:
    pass   
    return Comment_data
    

    
 #get_playlist_details
def get_playlist_details(chanel_id):
       next_page_token=None
       All_data=[]
       while True:
              request=youtube.playlists().list(
                     part='snippet,contentDetails',
                     channelId=chanel_id,
                     maxResults=50,
                     pageToken=next_page_token
              )
              response=request.execute()

              for item in response['items']:
                     data=dict(Playlist_Id=item['id'],
                               Tittle=item['snippet']['title'],
                               Channel_Id=item['snippet']['channelId'],
                               Channel_Name=item['snippet']['channelTitle'],
                               PublishedAt=item['snippet']['publishedAt'],
                               Video_Count=item['contentDetails']['itemCount'])
                     All_data.append(data)

              next_page_token=response.get('nextPageToken')
              if next_page_token is None:
                     break
       return All_data


#upload to mongodb
client=pymongo.MongoClient("mongodb://localhost:27017")
db=client["Youtube_data"]


def channel_details(channel_id):
    ch_details=get_channel_info(channel_id)
    pl_details=get_playlist_details(channel_id)
    vi_ids=get_video_ids(channel_id)
    vi_details=get_video_info(vi_ids)
    com_details=get_comment_info(vi_ids)

    coll1=db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,
                      "video_information":vi_details,"comment_information":com_details})
    
    return "upload completed sucessfully"


#Table creation for channels , playlists,videos, comments
def channels_table():
        mydb=psycopg2.connect(host="localhost",
                                user="postgres",
                                password="gokul",
                                database="youtubeproject",
                                port="5432")
        cursor=mydb.cursor()
        mydb.commit()

        drop = "drop table if exists channels"
        cursor.execute(drop)
        mydb.commit()
        create_query='''create table if not exists channels(channel_Name varchar(1000),
                                                                        Channel_id varchar(1000) primary key,
                                                                        Subscribers bigint,
                                                                        Views bigint,
                                                                        Total_Videos int,
                                                                        Channel_Description text,
                                                                        Playlist_id varchar(80))'''
        cursor.execute(create_query)
        mydb.commit()


        ch_list=[]
        db=client["Youtube_data"]
        coll1=db["channel_details"]
        for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
                ch_list.append(ch_data["channel_information"])
        df=pd.DataFrame(ch_list)
        

        for index,row in df.iterrows(): 
                        insert_query='''insert into channels(channel_Name,
                                                        Channel_id ,
                                                        Subscribers,
                                                        Views ,
                                                        Total_Videos,
                                                        Channel_Description ,
                                                        Playlist_id)
                                                        
                                                        
                                                        
                                                        
                                                        values(%s,%s,%s,%s,%s,%s,%s)'''
                        

                        
                        values=(row['channel_Name'],
                                row['Channel_id'],
                                row['Subscribers'],
                                row['Views'],
                                row['Total_Videos'],
                                row['Channel_Description'],
                                row['Playlist_id'])
            

                        cursor.execute(insert_query,values)    
                        mydb.commit()

        print("Channel value are already inserted")



def playlist_table():

        mydb=psycopg2.connect(host="localhost",
                                user="postgres",
                                password="gokul",
                                database="youtubeproject",
                                port="5432")
        cursor=mydb.cursor()
        mydb.commit()
        drop = "drop table if exists playlists"
        cursor.execute(drop)
        mydb.commit()
        create_query='''create table if not exists playlists(Playlist_Id varchar(1000) primary key,
                                                                        Tittle varchar(100),
                                                                        Channel_Id varchar(100),
                                                                        Channel_Name varchar(100),
                                                                        PublishedAt timestamp,
                                                                        Video_Count int
                                                                        )'''
        cursor.execute(create_query)
        mydb.commit()


        pl_list=[]
        db=client["Youtube_data"]
        coll1=db["channel_details"]
        for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
         for i in range(len(pl_data['playlist_information'])):
                pl_list.append(pl_data["playlist_information"][i])
        df1=pd.DataFrame(pl_list)
        
        for index,row in df1.iterrows():
               
                insert_query='''insert into playlists(Playlist_Id,
                                         Tittle,
                                         Channel_Id,
                                         Channel_Name,
                                         PublishedAt,
                                         Video_Count 
                                         )
                                         
                                         
                                         
                                         values(%s,%s,%s,%s,%s,%s)'''
                values=(row['Playlist_Id'],
                        row['Tittle'],
                        row['Channel_Id'],
                        row['Channel_Name'],
                        row['PublishedAt'],
                        row['Video_Count']
                        )
                

                cursor.execute(insert_query,values)
                mydb.commit()


def video_tables():
    mydb=psycopg2.connect(host="localhost",
                                user="postgres",
                                password="gokul",
                                database="youtubeproject",
                                port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query='''create table if not exists videos(Channel_Name varchar(100),
                                                Channel_id varchar(100),
                                                video_Id varchar(30)primary key,
                                                Title varchar(100),
                                                Tags text,
                                                Thumbnails varchar(200),
                                                Descripition text,
                                                Published_Date timestamp,
                                                Duration interval,
                                                Views bigint,
                                                Likes bigint,
                                                Comments int,
                                                Favorite_Count int,
                                                Definition varchar(10),
                                                Caption_Status varchar(50)
                                                    )'''
    cursor.execute(create_query)
    mydb.commit()    


    vi_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data['video_information'])):
            vi_list.append(vi_data["video_information"][i])
        df2=pd.DataFrame (vi_list) 

        
    vi_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data['video_information'])):
            vi_list.append(vi_data["video_information"][i])

    df2=pd.DataFrame (vi_list) 

        
    for index,row in df2.iterrows():
                insert_query='''insert into videos(Channel_Name,
                                                        Channel_id,
                                                        video_Id,
                                                        Title,
                                                        Tags,
                                                        Thumbnails,
                                                        Descripition,
                                                        Published_Date,
                                                        Duration,
                                                        Views,
                                                        Likes,
                                                        Comments,
                                                        Favorite_Count,
                                                        Definition,
                                                        Caption_Status  
                                                                
                                                        )    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                
                values=(row['Channel_Name'],
                                    row['Channel_id'],
                                    row['video_Id'],
                                    row['Title'],
                                    row['Tags'],
                                    row['Thumbnails'],
                                    row['Descripition'],
                                    row['Published_Dates'],
                                    row['Duration'],
                                    row['Views'],
                                    row['Likes'],
                                    row['Comments'],
                                    row['Favorite_Count'],
                                    row['Definition'],
                                    row['Caption_Status']
                                    )

                cursor.execute(insert_query,values)
                mydb.commit()

def comments_tables():

    mydb=psycopg2.connect(host="localhost",
                                    user="postgres",
                                    password="gokul",
                                    database="youtubeproject",
                                    port="5432")
    cursor=mydb.cursor()
    mydb.commit()
    drop = "drop table if exists comments"
    cursor.execute(drop)
    mydb.commit()
    create_query='''create table if not exists comments(Channel_Id varchar(100),
                                                        Video_Id varchar(50),
                                                        Comment_Text text ,
                                                        Comment_Author varchar(100),
                                                        Comment_Published timestamp
                                                            )'''
    cursor.execute(create_query)
    mydb.commit()


    com_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data['comment_information'])):
            com_list.append(com_data["comment_information"][i])
        df3=pd.DataFrame(com_list) 


    for index,row in df3.iterrows():
             insert_query='''insert into comments(Channel_Id,
                                                        Video_Id,
                                                        Comment_Text,
                                                        Comment_Author,
                                                        Comment_Published
                                            )
                                        
                                        
                                        
                                        values(%s,%s,%s,%s,%s)'''
             values=(row['Channel_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                        row['Comment_Author'],
                        row['Comment_Published']
                        )
                

             cursor.execute(insert_query,values)
             mydb.commit()


def tables():
    channels_table()
    playlist_table()
    video_tables()
    comments_tables()
    
    return "Table Created Sucessfully"

def show_channels_tables():
    ch_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)
    return df

def show_playlists_tables():
    pl_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data['playlist_information'])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=st.dataframe(pl_list)
    return df1

def show_videos_tables():
    vi_list=[]
    db=client["Youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data['video_information'])):
            vi_list.append(vi_data["video_information"][i])
    df2=st.dataframe(vi_list) 
    return df2 

def show_comments_tables():
     com_list=[]
     db=client["Youtube_data"]
     coll1=db["channel_details"]
     for com_data in coll1.find({},{"_id":0,"comment_information":1}):
            for i in range(len(com_data['comment_information'])):
                com_list.append(com_data["comment_information"][i])
     df3=st.dataframe(com_list) 
     return df3   

#streamlit part
with st.sidebar:
    st.title(":black[YOUTUBE DATA HAVERSTING AND WAREHOUSING]")
    st.header("skill Take Away")
    st.caption("python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management using MongoDB and sql")



channel_id=st.text_input("Enter the channel ID")

if st.button("Collect and store data"):
   ch_ids=[]
   db=client["Youtube_data"]
   coll1=db["channel_details"]
   for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
      ch_ids.append(ch_data["channel_information"]["Channel_id"])

   if channel_id in ch_ids:
        st.success("Channel Details of the given channel id already exists")
   else:
       insert=channel_details(channel_id)
       st.success(insert)


if st.button("Migrate to sql"):  
   Table=tables() 
   st.success(Table) 

show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))


if show_table=="CHANNELS":
     show_channels_tables()

elif show_table=="PLAYLISTS":
   show_playlists_tables()

elif show_table=="VIDEOS":
   show_videos_tables()

elif show_table=="COMMENTS":
     show_comments_tables()


#sql Connection
mydb=psycopg2.connect(host="localhost",
                                    user="postgres",
                                    password="gokul",
                                    database="youtubeproject",
                                    port="5432")
cursor=mydb.cursor()

question=st.selectbox("Select your question",("1.All the videos and the the channel name",
                                                 "2.channela with most number of videos",
                                                 "3.10 most viewd videos",
                                                 "4.comments in each videos",
                                                 "5.videos with higest likes",
                                                 "6.likes of all videos",
                                                 "7.views of each channel",
                                                 "8.videos published in the year of 2022",
                                                 "9.average duration of all videos in each channel",
                                                "10.videos with highest number of comments"))

if question=="1.All the videos and the the channel name":
    query1='''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)

elif question=="2.channela with most number of videos":
    query2='''SELECT channel_name AS channelname, total_videos AS no_videos 
            FROM channels 
            ORDER BY total_videos DESC'''
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","no of videos"])
    st.write(df2)    

elif question=="3.10 most viewd videos":
    query3='''select views as view , channel_name as channelname,title as videotitle from videos
                where views is not null order by views desc limit 10'''
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channel name","videotitle"])    
    st.write(df3)

elif question=="4.comments in each videos":
    query4='''select comments as no_comments,title as videotitle from videos where comments is not null '''
    cursor.execute(query4)
    mydb.commit()
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4,columns=["no of comments","videotitle"])    
    st.write(df4)
elif question == "5.videos with highest likes":
    query5 = '''select title as videotitle, channel_name as channelname, likes as likecount
                from videos where likes is not null order by likes desc'''
    cursor.execute(query5)
    mydb.commit()
    t5 = cursor.fetchall()
    df5 = pd.DataFrame(t5, columns=["videotitle", "channelname", "likecount"])    
    st.write(df5)

elif question == "6.likes of all videos":
    query6 = '''select likes as likecount, title as videotitle from videos'''
    cursor.execute(query6)
    mydb.commit()
    t6 = cursor.fetchall()
    df6 = pd.DataFrame(t6, columns=["likecount","videotitle"])
    st.write(df6)

elif question == "7.views of each channel":
    query7= '''SELECT channel_name AS channelname, views AS totalviews FROM channels'''
    cursor.execute(query7)
    mydb.commit()
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7, columns=["channel name", "totalviews"])
    st.write(df7)

elif question ==  "8.videos published in the year of 2022":
    query8 = '''select title as videos_title,published_date as videorelease,channel_name as channelname from videos
                where extract (year from published_date)=2022 '''
    cursor.execute(query8)
    mydb.commit()
    t8= cursor.fetchall()
    df8 = pd.DataFrame(t8, columns=["videotitle","published_date","channelname"])
    st.write(df8)

elif question == "9.average duration of all videos in each channel":
    query9= '''select channel_name as chennalname,AVG(duration) as averageduration from videos group by channel_name '''
    cursor.execute(query9)
    mydb.commit()
    t9= cursor.fetchall()
    df9 = pd.DataFrame(t9, columns=["channelname","averageduration"])

    T9=[]
    for index,row in df9.iterrows():
        channel_title=row["channelname"]
        average_duration=row["averageduration"]
        average_duration_str=str(average_duration)
        T9.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
    df1=pd.DataFrame(T9)
    st.write(df1)

elif question == "10.videos with highest number of comments":
    query10= '''SELECT title AS videotitle, channel_name AS channelname, comments AS comments 
                FROM videos 
                WHERE comments IS NOT NULL 
                ORDER BY comments DESC '''
    cursor.execute(query10)
    mydb.commit()
    t10= cursor.fetchall()
    df10 = pd.DataFrame(t10, columns=["video title","channel name","comments"])
    st.write(df10)



