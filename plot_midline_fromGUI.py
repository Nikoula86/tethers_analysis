#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 15:51:21 2019
@author: ngritti
"""

import numpy as np
#import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from tqdm import tqdm
from time import time
import glob, os, sys, pickle

def compute_rot_mat(d,th):
    ct = np.cos(th)
    st = np.sin(th)
    ct_d = 1-ct
    r1 = np.array( [ ct+d[0]*d[0]*ct_d, d[0]*d[1]*ct_d-d[2]*st, d[0]*d[2]*ct_d+d[1]*st ] )
    r2 = np.array( [ d[0]*d[1]*ct_d+d[2]*st, ct+d[1]*d[1]*ct_d, d[1]*d[2]*ct_d-d[0]*st ] )
    r3 = np.array( [ d[0]*d[2]*ct_d-d[1]*st, d[1]*d[2]*ct_d+d[0]*st, ct+d[2]*d[2]*ct_d ] )
    return np.stack([r1,r2,r3])

class Midline(object):
    
    def __init__(self, coords_file):
        self.coords_file = coords_file
        self.pxlsize = [0.41, 0.41, 2.]
        self.coords_anchors = pickle.load(open(coords_file,'rb'))['Midline']
        # adjust pixel size
        if self.coords_anchors.shape[0] > 0:
            self.coords_anchors[:,0] *= self.pxlsize[0]
            self.coords_anchors[:,1] *= self.pxlsize[1]
            self.coords_anchors[:,2] *= self.pxlsize[2]
        
    #%% 
    def setup_figure(self, figsize=(10,5),viewpoint=(45,60),
        axoff = True):

        fig = plt.figure(figsize=figsize)
        plt.subplots_adjust(left=0.,bottom=0.,right=1.,top=1.)
        plt.style.use('dark_background')
        ax = fig.add_subplot(111, projection='3d')

        if axoff:
            ax.grid(False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_zticks([])
            ax.set_axis_off() 
        ax.set_xlim([0,450])
        ax.set_ylim([-50,250])
        ax.set_zlim([200,500])
        ax.view_init(*viewpoint)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        return fig, ax

    def extract_midline_coord_system(self, phase = -1,
                    plot = True, figsize = (10,5), viewpoint=(30,60), vect_length=10, n_vect_show=20, axoff=True,
                    smooth_order = 100, interp_order=3, method= 'pt'):
        assert(method in ['fs','pt']), 'Invalid method!'

        # select the midline in the specified contraction phase. If not specified, use the first one available
        centroid = np.copy(self.coords_anchors)
        if phase==-1:
            phase = np.min(centroid[:,3])
        centroid = centroid[centroid[:,3]==phase][:,:3]
        
        # # spline interpolation
        from scipy import interpolate
        tck, u = interpolate.splprep(np.transpose(centroid), s=smooth_order, k=interp_order)
        # first, compute a very fine spline
        u_fine = np.linspace(0,1.,10000)
        z_fine, y_fine, x_fine = interpolate.splev(u_fine, tck)
        S = np.transpose( np.array( [z_fine,y_fine,x_fine] ) )
        spline_length = np.sum(np.linalg.norm(np.diff(S,axis=0),axis=1))
        # print('Spline length with %d points: %.3f'%(10000, spline_length) )
        n_points_spline = int(spline_length)
        # then, compute the spline only on the right amount of points, i.e. such that they are homogeneously spaced 1pxl
        u_fine = np.linspace(0,1.,n_points_spline)
        z_fine, y_fine, x_fine = interpolate.splev(u_fine, tck)
        S = np.transpose( np.array( [z_fine,y_fine,x_fine] ) )
        
        # Compute all tangents 
        T = np.gradient(S,edge_order=2,axis=0)
        T = np.array( [ t/np.linalg.norm(t) for t in T ] )

        if method == 'fs': # frenet-serret frame
            N = np.gradient(T,edge_order=2,axis=0)
            N = np.array( [ n/np.linalg.norm(n) for n in N ] )

        elif method == 'pt': # parallel-transported frame, based on https://janakiev.com/blog/framing-parametric-curves/
            N = np.gradient(T,edge_order=2,axis=0)
            N = np.array( [ n/np.linalg.norm(n) for n in N ] )
            for i in range(n_points_spline - 1):
                b = np.cross(T[i], T[i + 1]) # compute cross product of consecutive tangents
                b = b / np.linalg.norm(b) # normalize vectore
                phi = np.arccos(np.dot(T[i], T[i + 1])) # compute angle between consecutive tangent
                R = compute_rot_mat(b,phi) # compute 3D rotation matrix
                N[i + 1] = np.dot(R, N[i]) # rotate previous N and save it as current N
                
        # Calculate the second normal vector B
        B = np.array([np.cross(t, n) for (t, n) in zip(T, N)])

        # plot everything
        if plot:
            fig, ax = self.setup_figure(figsize,viewpoint,axoff=axoff)
            show_step = int(n_points_spline/n_vect_show)
            ax.plot(centroid[:,0],centroid[:,1],centroid[:,2],'o',color='white',alpha=.3,ms=3)
            ax.plot(S[:,0],S[:,1],S[:,2],'-',color='white',lw=2,alpha=.6)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                T[::show_step,0],T[::show_step,1],T[::show_step,2],
                color='g',length=10,lw=1)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                N[::show_step,0],N[::show_step,1],N[::show_step,2],
                color='b',length=10,lw=1)
            ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
                B[::show_step,0],B[::show_step,1],B[::show_step,2],
                color='r',length=10,lw=1)

        # check if vectors are hortogonal and unitary
        # for t,n,b in zip(T,N,B):
        #     print('(t,n), (n,b), (t,b) angles: ',np.sum(t*n),np.sum(b*n),np.sum(t*b))
        #     print('t,n,b lengths: ',np.sum(t*t),np.sum(n*n),np.sum(b*b))

        # plt.show()
        return n_points_spline, S, T, N, B


#%%
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0), (0, 1))
            1.5707963267948966
            >>> angle_between((1, 0), (1, 0))
            0.0
            >>> angle_between((1, 0), (-1, 0))
            3.141592653589793
    """
    dot = np.dot(v1,v2)
    det = v1[0]*v2[1]-v1[1]*v2[0]
    return np.arctan2(det,dot)

def vector(p1,p2):

    return p2-p1

#%%

class Tethers(object):
    
    def __init__(self, coords_file):
        self.coords_file = coords_file
        self.pxlsize = [0.41, 0.41, 2.]
        self.coords_anchors = pickle.load(open(coords_file,'rb'))
        # adjust pixel size
        for _id in self.coords_anchors.keys():
            if self.coords_anchors[_id].shape[0] > 0:
                self.coords_anchors[_id][:,0] *= self.pxlsize[0]
                self.coords_anchors[_id][:,1] *= self.pxlsize[1]
                self.coords_anchors[_id][:,2] *= self.pxlsize[2]

    #%% Plot data in 3D
    
    def plot_XYZ_single_phase(self, phase = -1, chambers=['Atrium','Ventricle'],
                figure = None, setlims=False, xlim=(0,1000), ylim=(0,1000), alpha=0.5, ms=6,
                method='pt'):
        if phase==-1:
            phase = np.min(self.coords_anchors['Midline'][:,3])
        points_phase = self.filter_points_by_phase(self.coords_anchors,phase=phase)

        if figure == None:
            fig = plt.figure(figsize=(5,5))
            plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
            ax = fig.add_subplot(111, projection='3d')
        else:
            (fig,ax) = figure

        refs = points_phase['AVCanal'][:,:3]
        ax.plot(refs[:,0],refs[:,1],refs[:,2],'ok',ms=5)
        lines=[]
        for chn in chambers:
            if points_phase['tether_'+chn].shape[0] > 0:
                tethers = points_phase['tether_'+chn][:,:3]
                if chn=='Atrium':
                    color = '#1f77b4'
                elif chn=='Ventricle':
                    color = '#ff7f0e'
                    
                l,=ax.plot(tethers[:,0],tethers[:,1],tethers[:,2],
                               'o', ms=ms, mew=0.,
                               color=color, alpha=alpha,
                               label=chn)
                lines.append(l)

        midline = Midline(self.coords_file)
        n_points_spline,S,T,N,B = midline.extract_midline_coord_system(smooth_order=100, plot=False, method=method)
        show_step = int(n_points_spline/10)
        ax.plot(S[:,0],S[:,1],S[:,2],'-',color='black',lw=2,alpha=.6)
        ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
            T[::show_step,0],T[::show_step,1],T[::show_step,2],
            color='g',length=5,lw=1)
        ax.quiver(S[::show_step,0],S[::show_step,1],S[::show_step,2], 
            N[::show_step,0],N[::show_step,1],N[::show_step,2],
            color='b',length=5,lw=1)
        if setlims:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
        else:
            ax.set_xlim(auto=True)
            ax.set_ylim(auto=True)
        ax.legend(handles=lines)
    
    def plot_XYZ_all_phases(self, method = 'pt'):
        phase = set(self.coords_anchors['Midline'][:,3])

        fig = plt.figure(figsize=(5,5))
        plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
        ax = fig.add_subplot(111, projection='3d')

        for ph in phase:
            self.plot_XYZ_single_phase(phase=ph,method=method,figure=(fig,ax))

    #%% plot 2D coords

    def plot_SAP_single_phase(self, phase = -1, figure = None, colors = ['#1f77b4', '#ff7f0e' ], ms=5):
        if phase==-1:
            phase = np.min(self.coords_anchors['Midline'][:,3])
        points_phase = self.filter_points_by_phase(self.coords_anchors,phase=phase)

        if figure == None:
            fig = plt.figure(figsize=(5,5))
            plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
            ax = fig.add_subplot(111)
        else:
            (fig,ax) = figure
        ax.set_ylim(0,1)

        points_sap = self.extract_tethers2D_single_phase(phase=phase,method=method)
        print(points_sap)

        for i, ch in enumerate( ['tether_Atrium','tether_Ventricle'] ):
            if points_sap[ch].shape[0]>0:
                l,=ax.plot(points_sap[ch][:,1],points_sap[ch][:,0],'o',color=colors[i],ms=ms)
        if colors[0]==colors[1]:
            color = colors[0]
        else:
            color = 'black'
        ax.plot([-180,180],[points_sap['AVCanal'][0,0],points_sap['AVCanal'][0,0]],'-',color=color)
        
        plt.legend(['Atrium','Ventricle','AVCanal'], loc='upper right', fontsize=7)
        plt.xlabel('Angle')
        plt.ylabel('Distance along the midline')

    def plot_SAP_all_phases(self):
        phases = set(self.coords_anchors['Midline'][:,3])

        fig = plt.figure(figsize=(5,5))
        plt.subplots_adjust(left=0.05,bottom=0.05,right=0.95,top=0.95)
        ax = fig.add_subplot(111)

        # make color-coded by phase contraction
        colors = [['#4477AA'],
                  ['#4477AA','#CC6677'],
                  ['#4477AA','#DDCC77','#CC6677'],
                  ['#4477AA','#117733','#DDCC77','#CC6677'],
                  ['#332288','#88CCEE','#117733','#DDCC77','#CC6677'],
                  ['#332288','#88CCEE','#117733','#DDCC77','#CC6677','#AA4499']]
        colors = colors[len(phases)-1]

        for i, ph in enumerate( phases ):
            self.plot_SAP_single_phase(phase=ph, figure=(fig,ax), colors = [colors[i],colors[i]])
       
    #%% coordinate system manipulation
    
    def filter_points_by_phase(self,coords,phase):

        points_phase = { _id: np.array([]) for _id in coords }
        for _id in coords.keys():
            if coords[_id].shape[0] > 0:
                points_phase[_id] = coords[_id][coords[_id][:,3]==phase][:,:3]

        assert points_phase['AVCanal'].shape[0]==1, 'Error, there can only be one AVCanal!'
        assert points_phase['Midline'].shape[0]>0, 'Error, Midline points are required!'

        return points_phase

    def extract_tethers2D_single_phase(self,phase=-1,smooth_order=100,method='pt'):
        # if no phase assigned, assign the first phase in which a midline is detected
        if phase==-1:
            phase = np.min(self.coords_anchors['Midline'][:,3])

        # filter the points in that phase
        points_phase = self.filter_points_by_phase(self.coords_anchors, phase)

        # compute the midline spline, tangent and normals
        midline = Midline(self.coords_file)
        n_points_spline,Spline,T,N,B = midline.extract_midline_coord_system(phase=phase,smooth_order=smooth_order, plot=False, method=method)
        s = np.linspace(0,1,n_points_spline)

        # compute 2D projection: length along the midline, angle to Normal
        points_sap = {} #s: length along curve, a: alpha, p: phase
        for chamber in ['tether_Atrium','tether_Ventricle','AVCanal']:
            ps_xyz = points_phase[chamber]
            ps_surf = []
            for tether in ps_xyz:
                dist = [np.linalg.norm(tether-spline) for spline in Spline]
                i = np.where(dist==np.min(dist))[0][0]
                ps_surf.append([s[i],angle_between(tether-Spline[i],N[i])*180/np.pi,phase])
            points_sap[chamber] = np.array(ps_surf)

        return points_sap


'''
The only input needed
'''
# paths = [ '180907_kdrlrasCherry_myl7radGFP_001_merged',
#     '180907_kdrlrasCherry_myl7radGFP_002_merged',
#     '180914_kdrlrasCherry_mylGFP_ZO1_3_merge',
#     '180914_kdrlrasCherry_mylGFP_ZO1_4_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_2_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_3_merge_good',
#     '180928_kdrlrasCherry_myl7rasGFP_paxillin_4_merge_good',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try1',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_003_merge/try2',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try1',
#     '181107_kdrlRasCherry_Myl7GFP_phalloidine647_001_merge/try2_better',
#     ]

# path = paths[3]


# midline = Midline('test_unwrap_heart/5D_merged_points.p')
# midline.fix_outliers(idx=3)
# midline.smooth_tube(sigma=5)
# midline.extract_midline_coord_system()

method = 'pt'
tethers = Tethers('test_unwrap_heart/5D_merged_points.p')
tethers.extract_tethers2D_single_phase( method=method )

tethers.plot_XYZ_single_phase(phase=0,xlim=(100,300),ylim=(0,200),method=method)
tethers.plot_XYZ_all_phases(method=method)
tethers.plot_SAP_all_phases()

plt.show()

