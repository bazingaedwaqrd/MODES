# -*- coding: cp936 -*-
from __future__ import print_function
import sys,os,re,gc,time
import numpy as np
from mpl_toolkits.basemap import shapefile
from __init__ import Spatial_Data,Station_Data,Level_Path,Tmp_Path
#------------------------------------------------------------------------------

def grid_to_144x73(lat1,lon1,zi,**args):
    '''
    ����˹�������ϲ�ֵ��144x73
    '''
    lon2 = args.pop("lon", np.arange(0, 360, 2.5, dtype=float) )
    lat2 = args.pop("lat", np.arange(90,-90-1,-2.5,dtype=float) )
    from matplotlib.mlab import griddata

    xi, yi = np.meshgrid(lon1,lat1)
    #zi = np.loadtxt('a.txt')

    #lon2 = np.arange(0, 360, 2.5, dtype=float)
    #lat2 = np.arange(90,-90-1,-2.5,dtype=float)

    #points = np.vstack((x2,y2)).T
    ##lat = np.arange(-90, 90+1, 2.5, dtype=float)

    #print('*'*40)
    #print xi.shape,yi.shape,zi.shape,lon2.shape,lat2
    zi = griddata(xi.flatten(),yi.flatten(),zi.flatten(),lon2,lat2)#,interp='linear')
    zi[0]=np.mean(zi[1])
    zi[-1]=np.mean(zi[-2])
    print('.'),
    return zi

#------------------------------------------------------------------------------
def griddata_scipy_idw(x, y, z, xi, yi,function='linear'):
    '''
    scipy��������Ȩ��ֵ
    'multiquadric': sqrt((r/self.epsilon)**2 + 1)  #����
    'inverse': 1.0/sqrt((r/self.epsilon)**2 + 1) #����
    'gaussian': exp(-(r/self.epsilon)**2) ����������ֵ
    'linear': r  #��
    'cubic': r**3 #��
    'quintic': r**5  #Ч�����ǿ��
    'thin_plate': r**2 * log(r)  �ܿ�����������ֵ
    '''
    x = x.astype(np.float32)
    y = y.astype(np.float32)
    z = z.astype(np.float32)
    xi = xi.astype(np.float32)
    yi = yi.astype(np.float32)

    (nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()
    from scipy.interpolate import Rbf
    interp = Rbf(x, y, z, function=function,epsilon=2)#linear
    zi = np.reshape(interp(xi, yi),(nx,ny))
    zi = zi.astype(np.float32)
    return zi


#------------------------------------------------------------------------------
def griddata_linear_rbf(x, y, z, xi, yi):
    '''
    ��ɢ���ֵΪ�����ĺ������ٶȽϿ�
    ��������޲�Ҫ����500x500�����
    '''
    x = x.astype(np.float32)
    y = y.astype(np.float32)
    z = z.astype(np.float32)
    xi = xi.astype(np.float32)
    yi = yi.astype(np.float32)
    (nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()


    dist = distance_matrix(x,y, xi,yi)
    #print 'dist shape =',dist.shape,dist.dtype

    # Mutual pariwise distances between observations
    internal_dist = distance_matrix(x,y,x,y)

    # Now solve for the weights such that mistfit at the observations is minimized
    weights = np.linalg.solve(internal_dist, z)
    #print(weights.dtype)
    # Multiply the weights for each interpolated point by the distances
    zi =  np.dot(dist.T, weights)
    #print(xi.shape,yi.shape, zi.shape)
    zi = zi.reshape(nx,ny)
    zi = zi.astype(np.float32)
    return zi


#-----------------�����----------------------
def griddata_kriging222(X,Y,Z,xi,yi):
    a_Range = xi.shape[0]+yi.shape[1]
    a_Range = a_Range/3.0
    (nx,ny)=xi.shape
    x1 = xi.flatten()
    y1 = yi.flatten()
    z1 = np.zeros_like(x1)
    z1 = z1.flatten()


    NUM=6
    for ii in range(len(x1)):
        print(x1[ii],y1[ii])
        X2 = X-x1[ii]
        Y2 = Y-y1[ii]
        D1 = np.sqrt(X2*X2+Y2*Y2)
        idx2 = np.argsort(D1)

        #print(np.vstack((D1,idx2)).T)

        #print(idx2<=NUM)

        X3 = X[idx2<=NUM ]
        Y3 = Y[idx2<=NUM ]
        Z3 = Z[idx2<=NUM ]
        #print(np.vstack((X3,Y3,Z3)).T)

        z1[ii]=od_kriging(X3,Y3,Z3,x1[ii],y1[ii],a_Range)
        #z1=od_kriging(X,Y,Z,x1[ii],y1[ii],a_Range)

    #sys.exit(0)
    zi = z1.reshape(nx,ny)

    return zi



#def kriging(range,mode,Z_s,resol,pos,c0,c1,side_len):
#def kriging(X,Y,Z,xi,yi,c0=1.5,c1=20, mode=2):
#-----------------��ͨ�����----------------------
def griddata_kriging(X,Y,Z,xi,yi,c0=1.5,c1=20, mode=2):
    '''''kriging------------------------------
       �������ӻ�������python�������޸ģ�����Ľ������
    '''
    a_Range = xi.shape[0]+yi.shape[1]
    #a_Ragne = len(X)
    a_Range = a_Range/3
    #a_Range = 25

    #a_Range Ϊ��� Range
    #ָ���򻯱����ڿռ��Ͼ�������Եķ�Χ���ڱ�̷�Χ֮�ڣ����ݾ�������ԣ����ڱ��֮�⣬����֮�以����أ����ڱ������Ĺ۲�ֵ���Թ��ƽ������Ӱ�졣

    item = len(X)-1
    #file1=open("data.txt","w")
    #---------initialize values--------
    #----�õ���Χ����-----

    # begin_row = range[0]
    # begin_col = range[1]
    # end_row = range[2]
    # end_col = range[3]

    dim = item +1
    #---�ֱ���-------

    value = np.ones((item+1,item+1))
    D = np.ones((item+1,1))
    Cd = np.zeros((item+1,item+1))

    i,j=0,0

    while i<item:
        j=i
        while j<item :
        #temp_i = pos[i]
            #temp_i_x = temp_i[0]
            #temp_i_y = temp_i[1]
            temp_i_x = X[i]
            temp_i_y = Y[i]

            #temp_j = pos[j]
            #temp_j_x = temp_j[0]
            #temp_j_y = temp_j[1]
            temp_j_x = X[j]
            temp_j_y = Y[j]

            test_t = (temp_i_x-temp_j_x)**2+(temp_i_y-temp_j_y)**2
            test_t = np.sqrt(test_t)
            #test_t = np.linalg.norm(np.array([temp_i_x-temp_j_x,temp_i_y-temp_j_y]))
            #np.linalg.norm(np.array([i_f-temp_k_x,j_f-temp_k_y]))

            Cd[i][j]= test_t #���ɼ������
            j=j+1
        i=i+1

    #print('Cd=',Cd.shape)

    #----------����ģ���±�����ʵ�֣�����v��----------------
    value[item][item]=0
    #print(value)
    #if 1==mode:
    #    value = np.where(Cd<a_Range,c0 + c1*(1.5*Cd/a_Range - 0.5*(Cd/a_Range)*(Cd/a_Range)*(Cd/a_Range)),c0+c1)

    i,j=0,0
    while i < item :
        j= i
        while j < item :
            if mode == 1 : #Spher mode
                if  Cd[i][j] < a_Range :
                    value[i][j] = value[j][i] = c0 + c1*(1.5*Cd[i][j]/a_Range - 0.5*(Cd[i][j]/a_Range)*(Cd[i][j]/a_Range)*(Cd[i][j]/a_Range))
                else:
                    value[i][j] = value[j][i] = c0 + c1
            if mode == 2: #  Expon mode
                value[i][j] = value[j][i] = c0 + c1*(1-np.exp(-3*Cd[i][j]/a_Range))
            if mode == 3:#Gauss mode
                pass
            j=j+1
        i=i+1
        #cnt_x = (end_row - begin_row)/resol_x#x���򲽳�
    #cnt_y = (end_col - begin_col)/resol_y#y���򲽳�
    #print cnt_x
    #print cnt_y
    print('value.shape=',value.shape)


    #sys.exit(0)
    #l = 0

    #print('resol_x=',resol_x)
    #print('resol_y=',resol_y)
    ###########################
    shape1 = xi.shape
    dat1 = np.zeros_like(xi)

    x2 = xi.flatten()
    y2 = yi.flatten()
    dat2 = dat1.flatten()

    for ii in xrange(len(x2)):

        #print(D)
        #print(D.shape)         print(value)
        #######################################

        #i_f=x2[ii]
        #j_f=y2[ii]

        temp_k_x = X#[k]
        temp_k_y = Y#[k]

        a1 = x2[ii] - X
        b1 = y2[ii] - Y
        test_t = np.sqrt(a1*a1+b1*b1)
        #test_t = np.linalg.norm(np.array([i_f -temp_k_x , j_f-temp_k_y] ))
        if(1==mode):
            D = np.where(test_t<a_Range,c0 + c1*(1.5*test_t/a_Range - 0.5*(test_t/a_Range)**3),c0+c1)
        if(2==mode):
            D = c0+ c1*(1-np.exp(-3*test_t/a_Range))
        if(3==mode):
            D = c0+ c1*(1-np.exp(-1*(3*test_t)**2/a_Range**2 ))
            #1-np.exp(-1*( (3*Cd[i][j])**2/a_Range*2 ) )
        D[-1]=1#����һ��1
        #print('111',test_t,test_t.shape,a1,b1,c1,D.shape)
        #sys.exit(0)

        ########################################
        #-----d v ������������ڼ���w
        #print(D)
        try :
            D = np.linalg.solve(value,D)
        except:
            print("Kinging linalg.solve error")

        #print(D)
        #sys.exit(0)
        #print(D.shape)
        test_t = np.sum(D*Z)

        dat2[ii]=test_t

    zi = dat2.reshape(shape1)
    return zi


#------------------------------------------------------------------------------
def griddata_linear_rbf_flatten(x, y, z, xi, yi):
    '''
    ��ɢ���ֵΪ�����ĺ������ٶȽϿ�
    ��������޲�Ҫ����500x500�����
    '''
    x = x.astype(np.float32)
    y = y.astype(np.float32)
    z = z.astype(np.float32)
    xi = xi.astype(np.float32)
    yi = yi.astype(np.float32)
    #(nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()


    dist = distance_matrix(x,y, xi,yi)
    #print 'dist shape =',dist.shape,dist.dtype

    # Mutual pariwise distances between observations
    internal_dist = distance_matrix(x,y,x,y)

    # Now solve for the weights such that mistfit at the observations is minimized
    weights = np.linalg.solve(internal_dist, z)
    #print(weights.dtype)
    # Multiply the weights for each interpolated point by the distances
    zi =  np.dot(dist.T, weights)
    #print(xi.shape,yi.shape, zi.shape)
    #zi = zi.reshape(nx,ny)
    zi = zi.astype(np.float32)
    return zi
#------------------------------------------------------------------------------
def griddata_linear_rbf2(x, y, z, xi, yi,function='linear'):

    x = x.astype(np.float32)
    y = y.astype(np.float32)
    z = z.astype(np.float32)
    xi = xi.astype(np.float32)
    yi = yi.astype(np.float32)

    (nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()
    from scipy.interpolate import Rbf
    interp = Rbf(x, y, z, epsilon=1)#linear
    zi = np.reshape(interp(xi, yi),(nx,ny))
    zi = zi.astype(np.float32)
    return zi



def distance_matrix(x0, y0, x1, y1):
    '''�������'''

    x0= x0.astype(np.float32)
    y0= y0.astype(np.float32)
    x1= x1.astype(np.float32)
    y1= y1.astype(np.float32)
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T

    # Make a distance matrix between pairwise observations
    # Note: from <http://stackoverflow.com/questions/1871536>
    # (Yay for ufuncs!)
    d0 = np.subtract.outer(obs[:,0], interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])
    #print 'hypot d0,d1',d0.shape,d1.shape,d0.dtype,d1.dtype
    return np.hypot(d0, d1)

#...............................................................................
class Invdisttree:
    """
    inverse-distance-weighted interpolation using KDTree:
invdisttree = Invdisttree( X, z )  -- data points, values
interpol = invdisttree( q, nnear=3, eps=0, p=1, weights=None, stat=0 )
    interpolates z from the 3 points nearest each query point q;
    For example, interpol[ a query point q ]
    finds the 3 data points nearest q, at distances d1 d2 d3
    and returns the IDW average of the values z1 z2 z3
        (z1/d1 + z2/d2 + z3/d3)
        / (1/d1 + 1/d2 + 1/d3)
        = .55 z1 + .27 z2 + .18 z3  for distances 1 2 3

    q may be one point, or a batch of points.
    eps: approximate nearest, dist <= (1 + eps) * true nearest
    p: use 1 / distance**p
    weights: optional multipliers for 1 / distance**p, of the same shape as q
    stat: accumulate wsum, wn for average weights

How many nearest neighbors should one take ?
a) start with 8 11 14 .. 28 in 2d 3d 4d .. 10d; see Wendel's formula
b) make 3 runs with nnear= e.g. 6 8 10, and look at the results --
    |interpol 6 - interpol 8| etc., or |f - interpol*| if you have f(q).
    I find that runtimes don't increase much at all with nnear -- ymmv.

p=1, p=2 ?
    p=2 weights nearer points more, farther points less.
    In 2d, the circles around query points have areas ~ distance**2,
    so p=2 is inverse-area weighting. For example,
        (z1/area1 + z2/area2 + z3/area3)
        / (1/area1 + 1/area2 + 1/area3)
        = .74 z1 + .18 z2 + .08 z3  for distances 1 2 3
    Similarly, in 3d, p=3 is inverse-volume weighting.

Scaling:
    if different X coordinates measure different things, Euclidean distance
    can be way off.  For example, if X0 is in the range 0 to 1
    but X1 0 to 1000, the X1 distances will swamp X0;
    rescale the data, i.e. make X0.std() ~= X1.std() .

A nice property of IDW is that it's scale-free around query points:
if I have values z1 z2 z3 from 3 points at distances d1 d2 d3,
the IDW average
    (z1/d1 + z2/d2 + z3/d3)
    / (1/d1 + 1/d2 + 1/d3)
is the same for distances 1 2 3, or 10 20 30 -- only the ratios matter.
In contrast, the commonly-used Gaussian kernel exp( - (distance/h)**2 )
is exceedingly sensitive to distance and to h.

    """
    # anykernel( dj / av dj ) is also scale-free
    # error analysis, |f(x) - idw(x)| ? todo: regular grid, nnear ndim+1, 2*ndim

    def __init__( self, X, z, leafsize=10, stat=0 ):
        assert len(X) == len(z), "len(X) %d != len(z) %d" % (len(X), len(z))
        from scipy.spatial import cKDTree as KDTree
        self.tree = KDTree( X, leafsize=leafsize )  # build the tree
        self.z = z
        self.stat = stat
        self.wn = 0
        self.wsum = None;

    def __call__( self, q, nnear=6, eps=0, p=1, weights=None ):
    # nnear nearest neighbours of each query point --
        q = np.asarray(q)
        qdim = q.ndim
        if qdim == 1:
            q = np.array([q])
        if self.wsum is None:
            self.wsum = np.zeros(nnear)

        self.distances, self.ix = self.tree.query( q, k=nnear, eps=eps )
        interpol = np.zeros( (len(self.distances),) + np.shape(self.z[0]) )
        jinterpol = 0
        for dist, ix in zip( self.distances, self.ix ):
            if nnear == 1:
                wz = self.z[ix]
            elif dist[0] < 1e-10:
                wz = self.z[ix[0]]
            else:  # weight z s by 1/dist --
                w = 1 / dist**p
                if weights is not None:
                    w *= weights[ix]  # >= 0
                w /= np.sum(w)
                wz = np.dot( w, self.z[ix] )
                if self.stat:
                    self.wn += 1
                    self.wsum += w
            interpol[jinterpol] = wz
            jinterpol += 1
        return interpol if qdim > 1  else interpol[0]

#------------------------------------------------------------------------------
def griddata_Invdisttree(x, y, z, xi, yi,**args):
    '''
      ��������ֵ
    '''
    Nnear = args.pop("Nnear", 8)   #Nnear = 8  # 8 2d, 11 3d => 5 % chance one-sided -- Wendel, mathoverflow.com
    leafsize = args.pop("leafsize", 10)  #    leafsize = 10
    eps = args.pop("eps",0.1) # eps = .1  # approximate nearest, dist <= (1 + eps) * true nearest
    p = args.pop("p",1) #  p = 1  # weights ~ 1 / distance**p

    (nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()

    obsxy = np.column_stack((x,y))
    askxy = np.column_stack((xi,yi))

    print(obsxy.shape,z.shape)

    invdisttree = Invdisttree( obsxy, z, leafsize=leafsize, stat=1 )
    print('invdisttree.shape=',invdisttree)
    interpol = invdisttree( askxy, nnear=Nnear, eps=eps, p=p )
    print('interpol.shape=',interpol.shape)

    interpol = interpol.reshape(nx,ny)
    return interpol


#------------------------------------------------------------------------------

def griddata_all(x,y,z,x1,y1,func='line_rbf'):
    '''
    �Ѹ��ֲ�ֵ�������ϵ�һ��
    scipy_idw
    line_rbf
    Invdisttree
    nat_grid
    '''

    xi, yi = np.meshgrid(x1, y1)


    if('nearest'==func):
        zi= griddata_nearest(x,y,z,xi,yi)

    if('griddata'==func):
        from matplotlib.mlab import griddata
        zi = griddata(x,y,z,x1,y1)

    if('kriging'==func):
        zi= griddata_kriging(x,y,z,xi,yi)

    if('scipy_idw'==func):
        zi= griddata_scipy_idw(x,y,z,xi,yi)

    if('line_rbf'==func):
        zi = griddata_linear_rbf(x,y,z,xi,yi)  #        grid3 = grid3.reshape((ny, nx))
        print(zi.shape,x.shape,y.shape,z.shape,xi.shape,yi.shape)
        #sys.exit(0)

    if('line_rbf2'==func):
        zi = griddata_linear_rbf2(x,y,z,xi,yi)  #        grid3 = grid3.reshape((ny, nx))


    if('Invdisttree'==func):
        #zi = df.griddata_Invdisttree(x,y,z,xi,yi,Nnear=15,p=3,eps=1)
        print(x.shape,y.shape,z.shape,x1.shape,y1.shape)
        #sys.exit(0)
        zi = griddata_Invdisttree(x,y,z,xi,yi,p=3)#,Nnear=10,eps=1)

    if('nat_grid'==func):
        from griddata import griddata, __version__
        zi = griddata(x,y,z,xi,yi)

    #if('test'==func):
    #    zi = griddata_scipy_spatial(x,y,z,xi,yi)

    return zi,xi,yi


#------------------------------------------------------------------------------
def extened_grid(zi,x1,y1,zoom=2):
    '''
    xinterval : X��ֵ�ļ��
    yinterval : Y ��ֵ�ļ��
    ��չ��������zoomΪ��չ����
    '''
    #print(x1)
    nx = np.size(x1)
    ny = np.size(y1)
    x2 = np.linspace(x1.min(), x1.max(), nx * zoom)
    y2 = np.linspace(y1.min(), y1.max(), ny * zoom)
    xi,yi = np.meshgrid(x2,y2)

    #��ֵ����1 Zoom����
    #from scipy import ndimage
    #z2 = ndimage.interpolation.zoom(zi[:,:], zoom)

    #��ֵ����2 basemap.interp����
    from mpl_toolkits.basemap import interp
    z2 = interp(zi, x1, y1, xi, yi, checkbounds=True, masked=False, order=1)

    #��ֵ����3 interpolate.RectBivariateSpline ���������ϵ������ƽ���
    # Bivariate spline approximation over a rectangular mesh
    #from scipy import interpolate
    #sp = interpolate.RectBivariateSpline(y1,x1,zi,kx=1, ky=1, s=0)
    #z2 = sp(y2,x2)

    #sp = interpolate.LSQBivariateSpline(y1,x1,zi)
    #z2 = sp(y2,x2)

    #terpolate.LSQBivariateSpline?

    print('extend shapes:=',z2.shape,xi.shape,yi.shape)
    return z2,xi,yi,x2,y2,nx*zoom,ny*zoom
    #print(x3)


#------------------------------------------------------------------------------
def draw_map_lines(m,shapefilename,color='k',linewidth =0.2,debug=0):
    '''
    m:basemap����
    shapefilename��Ϊshapefile������
    '''
    sf = shapefile.Reader(shapefilename)
    shapes = sf.shapes()
    i=0
    for shp in shapes:
        #print(i,end=' ') # i=i+1
        xy = np.array(shp.points)
        if(1==debug):
            #z4 = np.vstack((x,y4))
            #print(z4.shape)
            np.savetxt('n%d.txt'%i,xy,fmt='%6.2f')

        x4,y4=m(xy[:,0],xy[:,1])
        m.plot(x4,y4,color=color,linewidth=linewidth)
        #if(i>0):
        #    break


#------------------------------------------------------------------------------
def build_inside_mask_array(shapefilename,x1,y1):    #    r"spatialdat\china_province"
    '''
    #2011-11-12
    #���ø����shp�ļ�����һ����������mask�ƶ����������
    #----------------------------------------------------------------------
    #����һ�����飬ȫΪ������ֻ���й������ͼ
    '''
    import hashlib
    import matplotlib as mpl
    m1=hashlib.md5(str(x1)+str(y1)+shapefilename)
    #print(str(x1)+str(y1)+shapefilename)

    #�˴��Ѿ�����Ҫ��ȫ���洢��ȫ�ֱ���
    #if(not os.path.isdir('tmp')):
    #    os.mkdir("tmp")




    md5filename =os.path.join(Tmp_Path,'Z'+m1.hexdigest()+".npy")
    #print(md5filename)
    if(not os.path.isfile(md5filename)):
        #����ļ������ڣ������¼���mask����
        from mpl_toolkits.basemap import shapefile
        xi, yi = np.meshgrid(x1, y1)
        grid1 = np.ones_like(xi)
        grid1 = grid1<0
        #grid1 = grid1.flatten()
        sf = shapefile.Reader(shapefilename)
        shapes = sf.shapes()
        for shp in shapes:
            #see http://code.google.com/p/pyshp/
            #print(shp.bbox)
            srows = np.logical_and(x1>shp.bbox[0],x1<shp.bbox[2])
            scols = np.logical_and(y1>shp.bbox[1],y1<shp.bbox[3])
            selgrid =np.dot(np.atleast_2d(srows).T,np.atleast_2d(scols)).T
            #print(selgrid.shape,xi.shape,yi.shape,grid1.shape)

            points = np.vstack((xi[selgrid].flatten(),yi[selgrid].flatten())).T
            #print(mpl.__version__)
            #sys.exit(0)
            #�ж��Ƿ������������
            if  mpl.__version__ < '1.3.0':
                from matplotlib.nxutils import points_inside_poly
                grid2 = points_inside_poly(points, shp.points)
            else:
                from matplotlib.path import Path
                #import matplotlib.patches as patche
                #p=patchs.Polygon(shp.points)
                #p=Path(shp.points,closed=True)
                p=Path(shp.points)
                grid2 = p.contains_points(points)
                #grid2 = points_inside_poly(points, shp.points)

            grid1[selgrid] = np.logical_or(grid2,grid1[selgrid])
            #sys.exit(0)
        #�������
        np.save(md5filename,grid1)
        #print(grid1)
    else:
        grid1 = np.load(md5filename)
        #print(tmp_ary1)


    #----------------------------------------------------------------------
    #sys.exit(0)
    return  grid1#,shapes

#------------------------------------------------------------------------------
def griddata_nearest(x, y, z, xi, yi):
    x = x.astype(np.float32)
    y = y.astype(np.float32)
    z = z.astype(np.float32)
    xi = xi.astype(np.float32)
    yi = yi.astype(np.float32)

    print(type(yi))
    (nx,ny)=xi.shape
    xi, yi = xi.flatten(), yi.flatten()
    from scipy.interpolate import griddata
    interp = griddata((x, y), z,(xi,yi), method='nearest')#linear
    print(type(interp))
    print(interp.shape,nx,ny)

    interp = interp.flatten()

    zi = np.reshape(interp,(nx,ny))
    zi = zi.astype(np.float32)
    return zi

    #zi = np.reshape(interp(xi, yi),(nx,ny))