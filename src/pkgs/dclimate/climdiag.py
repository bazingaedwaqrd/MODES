# -*- coding: cp936 -*-
from __future__ import print_function
from __future__ import division

import numpy as np
import time as getsystime
from mpl_toolkits.basemap import Basemap,shapefile
import matplotlib.pyplot as plt
import netCDF4 as nc4
from dateutil.relativedelta import relativedelta
import sys,time
#
from dfunc import mytic,mytoc,save_obj,load_obj
import dplotlib as dplot
import dclimate as dclim
import dfunc as df
from  datetime import datetime
####

class climate_diagnosis():
    '''
    ����������ϵ���
    1 self.Region ���վ��ֵ����Ϊʱ�䣬��Ϊ�ռ�
    2 self.I_Year �����������
    3 self.StaLatLon : Sta lon lat  ������ֱ����
    4 self.Mon ���ڷ�����Ԥ�����·�
    5 self.Monts_Count �����µķ�����1Ϊ���� 2~3Ϊ����Ԥ��
    6 self.Field    NCEP����������
    7 self.lons ͳһ��γ��
    8 self.lats ͳһ�ľ���
    9 self.FieldP Ԥ��������γ�ȸ��һ��
    10 self.I_YearP Ԥ��������ݣ��п���ȷֵ 1982...2010 ����ȱ2009��2010��2011 CFS,TCC
    11 model_var_name ģʽ������

    //-----------------------------------

    11 self.r1,self.p1 ����Ԥ������͸߿ջ���������ؾ��� վ����� N x (144x73)
    12 self.r2,self.p2 �������͵���Ҫ�س������������ Ϊ 73x144

    13 self.r_np,self.p_np  NCEP�ٷ������Ϻ�Ԥ��������ط�����ʾ
    // -------------------------------------------------------
    14 self.p_np1  NCEP�����������Ҫ����صĳ��Ĺ��˾���Ϊ73x144 �ٷ�������Ҫ�س�
    15 self.p_np2  NCEP��������ģʽԤ��������س����˾���Ϊ 73x144  �ٷ�������ģʽԤ����

    16 self.p_np3  p_np1,p_np2�Ĺ�ͬ�����ŶȾ���

    17 self.X_Pre  Ԥ�����
    18 self.out    ������
    19 #ObjName ΪԤ����������
    '''

    def __init__(self,**arg):
        """
         ��ʵ���ʼ������,�������õ�������ʵ�廯
        """
        print('Init climate_diagnosis')
        self.Region = arg.pop('Region',None)
        self.I_Year = arg.pop('I_Year',None)
        print(self.I_Year)


        self.StaLatLon = arg.pop('StaLonLat',None)

        self.Mon = None
        self.Months_Count = None
        self.Field = None
        self.lons = np.arange(0, 360, 2.5, dtype=float)
        self.lats = np.arange(90, -90 - 1, -2.5, dtype=float)
        #ObjName ΪԤ����������
        self.ObjName = ''
        #��ȡ�ĸ߶ȳ���Ϣ
        self.Fieldinfo ={}

    def Init_Parameter(self,Model_info,Mon,Months_Count):
        '''
            ��ʼ��Ԥ���º�ʱ�β��������������»��Ǽ�
        '''

        self.Model_info = Model_info
        self.Mon = Mon
        self.Months_Count = Months_Count

    def Init_Sta_Dat(self,FileName):
        '''
            ��ʼ��վ������
        '''
        RegionR = np.loadtxt(FileName)
        self.Region = RegionR[1:,3:]
        self.I_Year = RegionR[0,3:]
        self.StaLatLon = RegionR[1:,0:3]
        print(self.Region.dtype)
        #print(I_Year.dtype)
        #print(stalonlat)
        self.I_Year_Show= self.I_Year[-1] #arg.pop('I_Year_Show',self.I_Year[-1]);
        print(self.I_Year_Show)

    def Init_Reanalysis_Field_Dat(self,FileName,Offset=0,**arg):
        '''
        ��netcdf�ļ��ж�ȡNCEP�ٷ�����������
        '''
        if None==self.Mon or None==self.Months_Count:
            print('Error Please Init Month value by "Init_Parameter(Mon,Months_Count)" Method')
            sys.exit(0)
        from dfunc import Read_Ncep_Hgt
        self.Field,self.Fieldinfo  = Read_Ncep_Hgt(FileName,I_Year=self.I_Year,\
                                             Mon=self.Mon,\
                                             Months_Count=self.Months_Count,FieldOffset=Offset,**arg)


    def Init_CFS_Field_Dat(self,FileName,**arg):
        '''

        '''
        self.model_var_name = arg['var_name']
        print(self.model_var_name)
        #sys.exit(0)
        self.FieldP,self.I_YearP = read_climate_model_dat(\
                                   FileName,self.I_Year,self.Mon,self.Months_Count,**arg)


    def Proc_Sta_Ncep_Cross_Corr(self):
        '''
        վ���ncep�߶ȳ����
        '''
        print('start station date corss corrlation with Field')
        shp1 = self.Field.shape
        Field2 = self.Field.reshape(shp1[0],-1)
        Field2 = Field2.T
        Region = self.Region
        print(Field2.shape)
        print(Region.shape)

        mytic()
        #����ʱ��Ƚϳ�
        #self.r1,self.p1=dclim.mcorr(Region[0,:],Field2)
        self.r1,self.p1=dclim.mcorr(Region,Field2)
        mytoc('corss corr:')

        print(self.r1.shape,self.p1.shape)

        #p2 = np.where(self.p1>0.05,0,1)  #���ڹ��˵��Ŷȼ�������
        p2 = np.mean(self.p1,axis=0)
        self.p2 = p2.reshape(73,-1)
        r2 = np.mean(self.r1,axis=0)     #���ڹ��˵��Ŷȼ�������
        self.r2 = r2.reshape(73,-1)
        print('End station date corss corrlation with Field')

    def Proc_Field_Ana_and_Field_Pred(self):
        '''
        �߶ȳ���Ԥ�������
        '''
        print('*'*80)
        I_Year = self.I_Year
        I_YearP = self.I_YearP
        print("NCEP Years\n",I_Year)
        print("Model Years\n",I_YearP)

        print("NCEP Date [0,0]:\n",self.Field[:,0,0])
        print("Model Date [0,0]:\n",self.FieldP[:,0,0])

        #sys.exit(0)

        FieldN = self.Field[np.in1d(I_Year,I_YearP),:,:]
        FieldP = self.FieldP[np.in1d(I_YearP,I_Year) ,:,:]

        print(self.Field.shape)
        print(FieldN.shape)
        print(self.FieldP.shape)
        print(FieldP.shape)
        m=FieldP.shape

        FieldN = FieldN.reshape(m[0],-1)
        FieldP = FieldP.reshape(m[0],-1)

        r_np=np.zeros(m[1]*m[2])
        p_np=np.zeros(m[1]*m[2]) #73*144
        
        from scipy.stats import pearsonr
        for i in range(m[1]*m[2]):
            r_np[i],p_np[i] = pearsonr(FieldN[:,i],FieldP[:,i])

        self.r_np = r_np.reshape((m[1],m[2]))
        self.p_np = p_np.reshape((m[1],m[2]))


    def Filter_Pred_from_corr(self,Threshold=0.10):
        '''
            ����Ԥ������ʵ���������
        '''
        p_np1 = np.where(self.p2<Threshold,True,False)
        p_np2 = np.where(self.p_np<Threshold,True,False)
        self.p_np1 = p_np1
        self.p_np2 = p_np2
        self.p_np3 = np.logical_and(p_np1,p_np2)  #np1�������㣬np2������������߼�����

        self.p_np3[38:,:]=False
        self.p_np3[:,72:]=False

        FieldP_Filter = np.copy(self.FieldP)
        FieldP_Filter[:,np.logical_not(self.p_np3)]=np.nan
        #FieldP_Filter[:,p_np1]=np.nan
        print('Filter_Pred_from_corr=',p_np2.shape,FieldP_Filter.shape)
        self.FieldP_Filter = FieldP_Filter


    def Pred_EOF_CCA(self):
        '''
        Ԥ��ģ�飬��Ҫ��һ�����ƣ��кܶ�������Ҫ��һ������
        '''

        I_Year = self.I_Year
        I_YearP = self.I_YearP
        print('I_Year=',I_Year)
        print('I_YearP=',I_YearP)
        #print(self.Field[:,0,0])
        #print(self.FieldP[:,0,0])

        #sys.exit(0)

        Region = self.Region[:,np.in1d(I_Year,I_YearP)]
        print('I_YearR=',I_Year[np.in1d(I_Year,I_YearP)])

        FieldP = self.FieldP[:,self.p_np3]  #���ڹ��˺�ĳ��ļ�
        FieldP = FieldP.T

        FieldP2 = FieldP[:,np.in1d(I_YearP,I_Year)]

        print(FieldP2.shape,np.atleast_2d(FieldP[:,-1]).T.shape)

        print('FieldP.shape = ',FieldP.shape)
        print('FieldP2.shape = ',FieldP2.shape)
        print('Region.shape = ',Region.shape)
        self.X_Pre = dclim.dpre_eof_cca(FieldP2,Region,np.atleast_2d(FieldP[:,-1]).T,4)
        print(self.X_Pre.shape)

        self.out = np.hstack((self.StaLatLon,self.X_Pre))
        
        print('Pred Year is ',I_YearP[-1])
        np.savetxt('out.txt',self.out,fmt='%5d %7.2f %7.2f %7.2f',delimiter=' ')

    #############################################################
    #�������---------�ǳ���Ҫ
    #for in range():
    #dclim.dpre_eof_cca(FieldP2,Region,np.atleast_2d(FieldP[:,-1]).T,4)
    #FieldP = [np.in1d(I_YearP,I_Year),self.p_np3]
    #print(Region.shape,FieldP.shape)
    #############################################################
    def Pred_EOF_CCA_Validation(self):
        '''
        ������֤ģ�飬��Ҫ��һ�����ƣ��кܶ�������Ҫ��һ������
        '''

        I_Year = self.I_Year
        I_YearP = np.array(self.I_YearP)
        print(I_Year,I_YearP)

        #print(self.Field[:,0,0])
        #print(self.FieldP[:,0,0])

        #sys.exit(0)

        #I_YearP2 = I_Year[np.in1d(I_Year,I_YearP)]
        I_YearP2 = I_YearP[np.in1d(I_YearP,I_Year)]
        #������ݶ���
        Region = self.Region[:,np.in1d(I_Year,I_YearP)]

        FieldP = self.FieldP[:,self.p_np3]
        FieldP = FieldP.T
        #������ݶ���
        FieldP2 = FieldP[:,np.in1d(I_YearP,I_Year)]
        print(FieldP2.shape,np.atleast_2d(FieldP[:,-1]).T.shape)


        print('FieldP.shape = ',FieldP.shape)
        print('FieldP2.shape = ',FieldP2.shape)
        print('Region.shape = ',Region.shape)

        shape1 = FieldP2.shape

        print(type(I_Year),type(I_YearP))
        #print(I_Year.shape,I_YearP.shape)
        #return

        PS= np.zeros((shape1[1]))
        SC= np.zeros((shape1[1]))
        ACC= np.zeros((shape1[1]))
        RMSE= np.zeros((shape1[1]))

        for i in range(shape1[1]):
            #continue
            FieldP3 = FieldP2
            FieldP2_H = np.delete(FieldP3,i,axis=1)
            FieldP2_P = FieldP2[:,i]

            Region2 = Region
            Region_P = Region2[:,i]
            Region_H = np.delete(Region2,i,axis=1)

            #print(FieldP2_H.shape,Region_H.shape)
            print('CCA Vali','%02d-Year=%04d'%(i,I_YearP[i]),end=' ')
            X_Pre = dclim.dpre_eof_cca(FieldP2_H,Region_H,np.atleast_2d(FieldP2_P).T,4)
            PS[i],SC[i],ACC[i],RMSE[i]=dclim.do_PS(X_Pre,Region_P,L1=20,L2=50)
            print('%5.2f,%5.2f,%5.2f,%5.2f'%(PS[i],SC[i],ACC[i],RMSE[i]))

        fig=plt.figure()
        #plt.plot(I_Year,SA,'-o', ms=5, lw=1, alpha=0.7, mfc='blue')

        plt.plot(I_YearP2,PS/100.0,'-*', ms=4, lw=2, alpha=0.7, mfc='blue')
        plt.plot(I_YearP2,SC,'-^', ms=4, lw=1.5, alpha=0.7, mfc='green')
        plt.bar(I_YearP2,ACC,color='blue',width=0.5)

        plt.xlim(I_YearP[0]-1,I_YearP[-1])

        cnfont = dclim.GetCnFont()
        ptitle = u'������� AVG PS=%5.2f,SC=%5.2f,ACC=%5.2f'%(np.mean(PS)/100.0,np.mean(SC),np.mean(ACC))
        plt.title(ptitle,fontproperties=cnfont)

        #ax=fig.add_subplot(111)
        plt.legend((u'PS','SC',u'ACC',),0,prop=cnfont)

        plt.hold(True)
        plt.grid()
        plt.savefig('Validation.png')
        df.CutPicWhiteBorder('Validation.png')
        plt.show()


    def Draw_Cross_Corr(self,ptitle='',func='ncep2sta',showimg=0):
        '''
        ���ƽ�����麯���ĺ���
        '''

        from dateutil.relativedelta import relativedelta

        datestr1 ='%04d-%02d-01'%(self.I_YearP[-1],self.Mon)
        date1 = datetime.strptime(datestr1,'%Y-%m-%d')
        date2 = date1+relativedelta(months=self.Months_Count-1)

        if(self.Months_Count>1):
            Title_DateStr1 = datetime.strftime(date1,' %b')+'-'+datetime.strftime(date2,'%b')
            
            Title_DateStr2 = datetime.strftime(date1,' %Y %b')
            for ii in range(self.Months_Count -1):
                Title_DateStr2 = Title_DateStr2+'-'+ datetime.strftime(date1+relativedelta(months=self.Months_Count-1-ii),'%b')
        else:
            Title_DateStr1 = datetime.strftime(date1,' %b')
            Title_DateStr2 = datetime.strftime(date1,' %Y-%b')


        imshow=showimg
        if 'sta_ncep_cross_corr'==func or 1==func:
            print(self.r2)
            dplot.drawhigh4corr(self.r2,self.lons,self.lats,ptype=1,\
                                ptitle=ptitle+u'վ����ٷ����������ͼ sta_ncep_cross_corr'+Title_DateStr1,\
                                imgfile='011SNCC.png',showimg=imshow)

        if 'sta_ncep_cross_corr_pval'==func or 2==func:
            dplot.drawhigh4corr(self.p2,self.lons,self.lats,ptype=1,\
                                ptitle=ptitle+u'վ����ٷ�����������Ŷ� sta_ncep_cross_corr_pval'+Title_DateStr1,\
                                imgfile='012SNCCP.png',showimg=imshow)

        if 'pred_ncep_corr'==func or 3==func:  #ģʽԤ�������ٷ����������ͼ
            dplot.drawhigh4corr(self.r_np,self.lons,self.lats,ptype=1,\
                                ptitle=ptitle+u'ģʽԤ�������ٷ����������ͼ pred_ncep_corr'+Title_DateStr1,\
                                imgfile='013PreNC.png',showimg=imshow)
            hgt7 = self.r_np
            hgt7 = np.where(hgt7<0.0,np.nan,hgt7)
            hgt7 = np.where(self.p_np>0.1,np.nan,hgt7)

            dplot.drawhigh4corr(hgt7,self.lons,self.lats,ptype=1,\
                                ptitle=ptitle+u'ģʽԤ�������ٷ����������ͼ pred_ncep_corr'+Title_DateStr1,\
                                imgfile='013PreNC_mask2.png',showimg=imshow)

            dplot.drawhigh4corr2(self.r_np,self.p_np,ptype=1,\
                                ptitle=ptitle+u'ģʽԤ�������ٷ����������ͼ pred_ncep_corr'+Title_DateStr1,\
                                imgfile='013PreNC_mask.png',showimg=imshow)

        if 'pred_ncep_corr_pval'==func or 4==func:
            dplot.drawhigh4corr(self.p_np,self.lons,self.lats,ptype=1,\
                                ptitle=ptitle+u'ģʽԤ�����ڷ������ͼ�Ŷ� pred_ncep_corr_pval'+Title_DateStr1,\
                                imgfile='014PreNCP.png',showimg=imshow)

        if  5==func:
            #��������ʵ��ֵ������500hPa�߶ȳ���ʵ�ʵ�ֵ
            #FieldP_end =self.FieldP_Filter[0,:,:]

            if(self.Months_Count>1):
                Title_DateStr1 = datetime.strftime(date1,' %b')+'-'+datetime.strftime(date2,'%b')

                Title_DateStr2 = datetime.strftime(date1,'YYYY %b')
                for ii in range(self.Months_Count -1):
                    Title_DateStr2 = Title_DateStr2+'-'+ datetime.strftime(date1+relativedelta(months=self.Months_Count-1-ii),'%b')
            else:
                Title_DateStr1 = datetime.strftime(date1,' %b')
                Title_DateStr2 = datetime.strftime(date1,' YYYY-%b')


            print(np.in1d(self.I_YearP,self.I_Year_Show))
            Ary_Sel_Year = np.in1d(self.I_YearP,self.I_Year_Show)
            print('&'*80)
            print(np.shape(self.I_YearP),np.shape(self.I_Year_Show))

            #FieldP_end =self.FieldP[-2,:,:]
            FieldP_end =self.FieldP[Ary_Sel_Year,:,:]
            FieldP_end =FieldP_end[0,:,:]

            #print(np.shape(FieldP_end[0,:,:]))
            #sys.exit(0)

            Title_DateStr2=Title_DateStr2.replace('YYYY','%04d'%self.I_Year_Show)

            #print(FieldP_end)
            #np.reshape(self.FieldP[0,:,:],(73,144))
            ptitle=self.Model_info +' forecast '+ self.model_var_name + ' '+Title_DateStr2
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,\
                           ptitle=ptitle,\
                                imgfile='015PreNCP_Real.png',showimg=imshow)


        if  6==func:
            #�������ľ�ƽֵ
            if(self.Months_Count>1):
                Title_DateStr1 = datetime.strftime(date1,' %b')+'-'+datetime.strftime(date2,'%b')

                Title_DateStr2 = datetime.strftime(date1,'YYYY %b')
                for ii in range(self.Months_Count -1):
                    Title_DateStr2 = Title_DateStr2+'-'+ datetime.strftime(date1+relativedelta(months=self.Months_Count-1-ii),'%b')
            else:
                Title_DateStr1 = datetime.strftime(date1,' %b')
                Title_DateStr2 = datetime.strftime(date1,' YYYY-%b')

            FieldP_avg = np.mean(self.FieldP[0:-1,:,:],axis=0)

            #print(np.in1d(self.I_YearP,self.I_Year_Show))
            Ary_Sel_Year = np.in1d(self.I_YearP,self.I_Year_Show)
            #print('&'*80)
            #print(np.shape(self.I_YearP),np.shape(self.I_Year_Show))
            #FieldP_end =self.FieldP[-2,:,:]
            FieldP_end =self.FieldP[Ary_Sel_Year,:,:]
            FieldP_end =FieldP_end[0,:,:]
            FieldP_end =FieldP_end - FieldP_avg


            #FieldP_end =self.FieldP[-1,:,:]- FieldP_avg

            FMax = np.max(FieldP_end.flatten())
            FMin = np.min(FieldP_end.flatten())

            if(abs(FMax)>abs(FMin)):
                TMax = FMax
            else:
                TMax = FMin

            import math
            TMax= math.ceil(TMax/10.0)
            TMax= TMax*10
            #lev1 = np.linspace(-1*TMax,TMax,11)
            TMax = 100
            lev1 = np.linspace(-TMax,TMax,21)  #NCC
            #cmap_str='RdYlBu' 'bwr'
            
            ptitle=self.Model_info +' forecast '+ self.model_var_name + ' Anomaly'+Title_DateStr2.replace('YYYY','%04d'%self.I_Year_Show)
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,\
                           ptitle=ptitle,imgfile='016PreNCP_Anomaly.png',showimg=imshow,cmap_str='seismic',lev=lev1)

        if  7==func:
            #�������������˵ľ�ƽֵ
            FieldP_avg = np.mean(self.FieldP_Filter[0:-1,:,:],axis=0)
            FieldP_end =self.FieldP_Filter[-1,:,:]- FieldP_avg
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,\
                           ptitle=ptitle+u'\npred_ncep_corr_pval'+Title_DateStr2,\
                                imgfile='017PreNCP_Anomaly_Filter.png',showimg=imshow)

        if  8==func:
            #���߶ȳ�������
            lev1 = np.array([5840,5880])
            FieldP_avg = np.mean(self.FieldP[0:-1,:,:],axis=0)
            FieldP_end =self.FieldP[-1,:,:]
            #����Ϊƽ��ֵ
            #����ΪԤ��ֵ
            ptitle=self.Model_info +' '+ self.model_var_name + ' 588 line avg and forecast'+Title_DateStr2
            dplot.drawhigh5880Line(FieldP_end,FieldP_avg,self.lons,self.lats,ptype=1,\
                           ptitle=ptitle,\
                                imgfile='018PreNCP_588line.png',showimg=imshow,lev=lev1)





#------------------------------------------------------------------------------
def read_climate_model_dat(FieldFileName,I_Year,Mon,Months_Count,var_name='hgt',ilev=5):
    print(FieldFileName)
    rootgrp = nc4.Dataset(FieldFileName,'r')
    print(rootgrp.file_format)
    #print rootgrp.variables
    print('----Start read model data---- '*4)

    lat = rootgrp.variables['lat'][:];
    lon = rootgrp.variables['lon'][:];
    #level = rootgrp.variables['level'][:];

    if 'level' in rootgrp.variables:
        level = rootgrp.variables['level'][:]
        dinfo["level"]=int(level[ilev])
    else:
        print("Can't find level variable")

    times = rootgrp.variables['time'];
    hgt = rootgrp.variables[var_name];

    #����netcdfʱ��ά����
    nc_date_str = nc4.num2date(times[:],units=times.units)
    from  datetime import datetime

    year1 = I_Year[0]
    I_Year2 = np.arange(year1,2050)
    #print(I_Year2)
    for tmpy in I_Year2:
        s1 ='%04d-%02d-01'%(tmpy,Mon)
        date1 = datetime.strptime(s1,'%Y-%m-%d')
        date2 = date1 + relativedelta(months=Months_Count-1)
        if(date2>nc_date_str.max()):
            break
        year2 = tmpy
        #print(date2)

    I_Year2 =  range(int(year1),int(year2)+1) #ѡ�������
    I_Year3 = []

    PField = np.zeros( (len(I_Year2),len(lat),len(lon)) )

    for i in range(len(nc_date_str)):
        datestr_c =  datetime.strftime(nc_date_str[i],'%Y-%m')
        #print(datestr_c)
        for tmpy in I_Year2:
            #print(tmpy)
            s1 ='%04d-%02d'%(tmpy,Mon)

            if s1==datestr_c:
                I_Year3.append(tmpy)
                L1 = i
                L2 = L1+Months_Count
                print(s1,'L1=',L1,'L2=',L2,end=' ')
                j=tmpy-I_Year2[0]    #ע���λ���ǳ���Ҫ����Ҫ�޸Ĵ˴�����
                print('%02d'%j,end=' ')
                ###Field[j,:,:]=np.mean(hgt[L1:L2,0,:,:],axis=0)
                print('data shape =',np.shape(hgt[L1:L2,:,:]),end='')  #�����ȡ����ֵ��ά��

                PField[j,:,:]=np.mean(hgt[L1:L2,:,:],axis=0)
                print(np.shape( PField[j,:,:] ))


    print(I_Year3)
    I_Year2 = np.array(I_Year2)
    PField = PField[np.in1d(I_Year2,I_Year3),:,:]

    shape1 = PField.shape
    for j in range(shape1[0]):
        print('mean pField',j,end=' ')
        print(np.mean(PField[j,:,:]))
        if(0==np.mean(PField[j,:,:])):
            PField[j,:,:]=np.nan
            PField = np.delete(PField,j,axis=0)
            I_Year3 = np.delete(I_Year3,j,axis=0)
            break


    print('len_I_Year=%d,len lat= %d,len lon =%d'%(len(I_Year3),len(lat),len(lon)) )
    print('read model Field Shape = ',PField.shape)
    rootgrp.close()
    print('--End read model data-- '*5)

    return PField,I_Year3

#--------------------------------------------------------------------------------
def calc_Siberian_hgt(Field,I_Year):
    '''
    �����������Ǹ�ѹ
    '''


    print(np.shape(Field))
    lons = np.arange(0, 360, 2.5, dtype=float)
    lats = np.arange(90, -90 - 1, -2.5, dtype=float)

    lat1 = np.where(lats < 60,True,False)
    lat2 = np.where(lats > 40,True,False)
    lat = np.logical_and(lat1,lat2)

    lon1 = np.where(lons < 120,True,False)
    lon2 = np.where(lons > 70,True,False)
    lon = np.logical_and(lon1,lon2)
    print(lat.shape,lon.shape)

    Field2 = Field[:,:,lon]
    Field2 = Field2[:,lat,:]
    n1 = Field2.shape
    Field2 = Field2.reshape(n1[0],-1)
    Field2=np.mean(Field2,axis=1)
    #Field2,a =dclim.mapstd(Field2)
    Field2  = Field2.flatten()
    print('c1=',Field2.shape)
    print('c2=',np.array(I_Year).shape)

    return Field2,np.array(I_Year)


#--------------------------------------------------------------------------------
def calc_India_Burma_througt(Field,I_Year):
    '''
    �����������Ǹ�ѹ
    '''
    print(np.shape(Field))
    lons = np.arange(0, 360, 2.5, dtype=float)
    lats = np.arange(90, -90 - 1, -2.5, dtype=float)

    lat1 = np.where(lats <= 20,True,False)
    lat2 = np.where(lats >= 15,True,False)
    lat = np.logical_and(lat1,lat2)

    lon1 = np.where(lons <= 100,True,False)
    lon2 = np.where(lons >= 80,True,False)
    lon = np.logical_and(lon1,lon2)
    print(lat.shape,lon.shape)

    Field2 = Field[:,:,lon]
    Field2 = Field2[:,lat,:]
    n1 = Field2.shape
    Field2 = Field2.reshape(n1[0],-1)
    Field2=np.mean(Field2,axis=1)
    Field2,a =dclim.mapstd(Field2)
    Field2  = Field2.flatten()
    print('c1=',Field2.shape)
    print('c2=',np.array(I_Year).shape)

    return Field2,np.array(I_Year)
#--------------------------------------------------------------------------------
'''
    def Draw_Cross_Corr_2(self,ptitle='Cross_Corr P-value',func='ncep2sta',showimg=1,title=''):

        #���ƽ�����麯���ĺ���

        imshow=showimg
        if 'sta_ncep_cross_corr'==func or 1==func:
            dplot.drawhigh4corr(self.r2,self.lons,self.lats,ptype=1,ptitle=title,\
                                imgfile='021SNCC.png',showimg=imshow)

        if 'sta_ncep_cross_corr_pval'==func or 2==func:
            dplot.drawhigh4corr(self.p2,self.lons,self.lats,ptype=1,ptitle=ptitle+'\nsta_ncep_cross_corr_pval',\
                                imgfile='022SNCCP.png',showimg=imshow)

        if 'pred_ncep_corr'==func or 3==func:
            dplot.drawhigh4corr(self.r_np,self.lons,self.lats,ptype=1,ptitle=ptitle+'\npred_ncep_corr',\
                                imgfile='023PreNC.png',showimg=imshow)

        if 'pred_ncep_corr_pval'==func or 4==func:
            dplot.drawhigh4corr(self.p_np,self.lons,self.lats,ptype=1,ptitle=ptitle+'\npred_ncep_corr_pval',\
                                imgfile='024PreNCP.png',showimg=imshow)

        if  5==func:
            FieldP_end =self.FieldP_Filter[0,:,:]
            #np.reshape(self.FieldP[0,:,:],(73,144))
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,ptitle=ptitle+'\npred_ncep_corr_pval',\
                                imgfile='025PreNCP_test.png',showimg=imshow)

        if  6==func:
            FieldP_avg = np.mean(self.FieldP[0:-1,:,:],axis=0)
            FieldP_end =self.FieldP[-1,:,:]- FieldP_avg
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,ptitle=ptitle+'\npred_ncep_corr_pval',\
                                imgfile='026PreNCP_anomaly.png',showimg=imshow)

        if  7==func:
            FieldP_avg = np.mean(self.FieldP_Filter[0:-1,:,:],axis=0)
            FieldP_end =self.FieldP_Filter[-1,:,:]- FieldP_avg
            dplot.drawhigh(FieldP_end,self.lons,self.lats,ptype=1,ptitle=ptitle+'\npred_ncep_corr_pval',\
                                imgfile='027PreNCP_anomaly_Filter.png',showimg=imshow)
'''
