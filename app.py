import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib import rc
from sklearn.neighbors import KernelDensity
import pickle
import random

urgentTypes = ['Unknown',
               'Non-operative neurologic',
               'Non-operative respiratory',
               'Non-operative cardiovascular',
               'Non-operative genitourinary',
               'Non-operative metabolic',
               'Non-operative Gastro-intestinal',
               'Post-operative gastro-intestinal',
               'Post-operative trauma',
               'Post-operative respiratory',
               'Post-operative neurologic',
               'Post-operative cardiovascular',
               'Post-operative genitourinary',
               'Post-operative musculoskeletal /skin',
               'Non-operative trauma',
               'Non-operative musculo-skeletal',
               'Post-operative transplant',
               'Non-operative hematological',
               'Post-operative hematology']

electiveTypes = ['Unknown',
                 'Non-operative metabolic',
                 'Non-operative cardiovascular',
                 'Non-operative respiratory',
                 'Non-operative Gastro-intestinal',
                 'Post-operative cardiovascular',
                 'Non-operative neurologic',
                 'Non-operative genitourinary',
                 'Post-operative gastro-intestinal',
                 'Non-operative hematological',
                 'Post-operative respiratory',
                 'Post-operative genitourinary',
                 'Post-operative metabolic',
                 'Post-operative trauma',
                 'Non-operative musculo-skeletal',
                 'Post-operative neurologic',
                 'Post-operative musculoskeletal /skin',
                 'Post-operative transplant',
                 'Non-operative transplant',
                 'Post-operative hematology',
                 'Non-operative trauma']

# Initialization function
def init():

  global time, total_patients, urgent_patients, elective_patients, allLoS, dischargedPatients, totalPatientsInICU, excessPatients, elective_kernels_LoS, urgent_kernels_LoS

  time = np.array([0])
  total_patients = np.array([0])
  urgent_patients = np.array([0])
  elective_patients = np.array([0])
  line1.set_data(time, total_patients)
  line2.set_data(time, urgent_patients)
  line3.set_data(time, elective_patients)
  txt_title.set_text('Frame = {0:4d}'.format(0))

  allLoS = np.array([0])
  dischargedPatients = 0
  totalPatientsInICU = 0
  excessPatients = 0

  with open('elective_kernels.pkl', 'rb') as f:
    elective_kernels_LoS = pickle.load(f)

  with open('urgent_kernels.pkl', 'rb') as f:
    urgent_kernels_LoS = pickle.load(f)

  return line1


# Using the pkl files
def modelLoS(patientsAdmitted, urgent, stopCardiac=False):
  global elective_kernels_LoS, urgent_kernels_LoS
  # Here I randomly select patients from the CSV file for urgent and non urgent
  if urgent:
    sampledUrgent = random.choices(urgentTypes, k=int(patientsAdmitted))
    urgentOutLoS = []
    for i in sampledUrgent:
      urgentOutLoS.append(np.ceil(urgent_kernels_LoS[i].sample(1)/24)) # Convert legth of stay in days
    return np.array(urgentOutLoS)
  else:
    if stopCardiac:
      sampledElective = random.choices(electiveTypes, k=int(patientsAdmitted))
      sampledElective = [t for t in sampledElective if t != 'Post-operative cardiovascular']
      electiveOutLoS = []
      for i in sampledElective:
        electiveOutLoS.append(np.ceil(elective_kernels_LoS[i].sample(1)/24)) # Convert legth of stay in days
      return np.array(electiveOutLoS)
    else:
      sampledElective = random.choices(electiveTypes, k=int(patientsAdmitted))
      electiveOutLoS = []
      for i in sampledElective:
        electiveOutLoS.append(np.ceil(elective_kernels_LoS[i].sample(1)/24)) # Convert legth of stay in days
      return np.array(electiveOutLoS)

def patientList(totalPatients, urgentPatients, electivePatients, n):

  global allLoS, dischargedPatients, totalPatientsInICU, excessPatients, numOfBeds

  # Weekends - We assume the day zero is Sunday - Weekends days: 6, 7, 13, 14, 20, 21, 27, 28, 34, 35 ...
  if ((n+1)%7==0) or (n%7==0):
    # number of admitted elective patients per day
    electivePatientsAdmitted = 0
    # number of admitted urgent patients per day
    urgentPatientsAdmitted = np.random.poisson(targeturgent, 1)
    totalPatientsInICU += urgentPatientsAdmitted[0]
    # predict the length for each of the admited patient
    allLoS = np.append(allLoS, n + modelLoS(urgentPatientsAdmitted, True))

  # Weekdays
  else:
    # number of admitted elective patients per day
    electivePatientsAdmitted = np.random.poisson(targetelective, 1)

    if cardiacon:

      # predict the length for each of the admited patient
      if n > cardiacstopday and n < cardiaccontinueday:
        LoSPredicted = modelLoS(electivePatientsAdmitted, False, True)
        allLoS = np.append(allLoS, n + LoSPredicted)
        totalPatientsInICU += len(LoSPredicted)
      else:
        LoSPredicted = modelLoS(electivePatientsAdmitted, False)
        allLoS = np.append(allLoS, n + LoSPredicted)
        totalPatientsInICU += len(LoSPredicted)

    else:

      LoSPredicted = modelLoS(electivePatientsAdmitted, False)
      allLoS = np.append(allLoS, n + LoSPredicted)
      totalPatientsInICU += len(LoSPredicted)

    # number of admitted urgent patients per day
    urgentPatientsAdmitted = np.random.poisson(targeturgent, 1)
    totalPatientsInICU += urgentPatientsAdmitted[0]
    # predict the length for each of the admited patient
    allLoS = np.append(allLoS, n + modelLoS(urgentPatientsAdmitted, True))

  if n == 1: # remove the initialization number
    allLoS = allLoS[1:]

  # Discharged the patients for this day (n)
  if n in allLoS:
    dischargedPatients = np.count_nonzero(allLoS == n)
    allLoS = allLoS[allLoS != n]
  else:
    dischargedPatients = 0

  # Reduce the patient count
  totalPatientsInICU -= dischargedPatients

  if totalPatientsInICU > numbeds:
    st.text(f"Alert in day {n}! - STOP admitting elective patients")
    st.text(f"Number of elective patients admitted on day {n} is {electivePatientsAdmitted}")

  # print(f"Number of total patients: {totalPatientsInICU}")
  # print(f"Number of patients discharged: {dischargedPatients}")

  urgentAdmissions = np.append(urgentPatients, urgentPatientsAdmitted)
  electiveAdmissions = np.append(electivePatients, electivePatientsAdmitted)
  totalICUPatients = np.append(totalPatients, totalPatientsInICU)

  return totalICUPatients, urgentAdmissions, electiveAdmissions


# simulation function. This is called sequentially
def ICUActivity(n):
    global time, total_patients, urgent_patients, elective_patients
    time = np.arange(0, n+1)
    if n > 0:
      total_patients, urgent_patients, elective_patients = patientList(total_patients, urgent_patients, elective_patients, n) # number of patients per day
    line1.set_data(time, total_patients)
    line2.set_data(time, urgent_patients)
    line3.set_data(time, elective_patients)
    txt_title.set_text('Frame = {0:4d}'.format(n))
    return line1


def animate(i):
    line1.set_ydata(data[i:max_x+i])
    the_plot.pyplot(plt)


st.title('Bed Bytes Simulation')  

numbeds = st.slider("How many beds?", 20, 50, 35, 1)
targetelective = st.number_input("How many elective admissions per day?", min_value=0.0, max_value=8.0, value=3.0, step=0.1)
targeturgent = st.number_input("How many urgent admissions per day?", 0.0, 5.0, 1.1, 0.5)
numdays = st.slider("How many days?", 200, 730, 365)
cardiacon = st.checkbox("Stop non-urgent cardiac surgery to release capacity?", value=True)
cardiacstopday = 50
cardiaccontinueday = cardiacstopday + 20

with st.form("simsettings"):
  if cardiacon:
     cardiacstopday = st.slider("Stop at how many days?", 0, numdays, value=100)
  
  st.write("Ideally this would be the % of capacity we're willing to accept")

  submitted = st.form_submit_button("Run")
  
if not submitted:
      st.stop()


# create a figure and axes
fig = plt.figure(figsize=(8,5))
ax1 = plt.subplot()

# set up the subplots as needed
ax1.set_xlim(( 0, numdays))
ax1.set_ylim((0, numbeds+10))
ax1.set_xlabel('Time (Days)')
ax1.set_ylabel('Number of ICU patients')
ax1.grid()

# create objects that will change in the animation. These are
# initially empty, and will be given new values for each frame
# in the animation.
txt_title = ax1.set_title('')
line1, = ax1.plot([], label='ICU Occupancy', color='#009E73', lw=2)
line2, = ax1.plot([], label='Urgent patients Admitted', color='#D55E00', lw=1.5)
line3, = ax1.plot([], label='Elective patients Admitted', color='#0072B2', lw=1.5)
ax1.axvline(x=cardiacstopday, ymin=0, ymax=numbeds, color='y')
ax1.axvline(x=cardiaccontinueday, ymin=0, ymax=numbeds, color='m')

ax1.legend(handles =[line1, line2, line3], loc ='upper right')

init()

anim = animation.FuncAnimation(fig, ICUActivity, init_func=init, frames=numdays+1, interval=20, blit=False)

st.title('Output simulation')
anim.save('output_animation.gif')

st.image('output_animation.gif')

st.title('Simulation with default values')
st.video('updatedSimulation.mp4', format="video/mp4", start_time=0)


